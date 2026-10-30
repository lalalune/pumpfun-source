use std::env;
use std::ffi::OsString;
use std::fs;
use std::io::{ErrorKind, Write};
use std::path::PathBuf;
use std::process::{self, Command};

fn json(value: &str) -> String {
    let mut out = String::from("\"");
    for c in value.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c < '\u{20}' => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

fn array(values: &[OsString]) -> String {
    format!("[{}]", values.iter().map(|v| json(v.to_str().expect("UTF-8 argument"))).collect::<Vec<_>>().join(","))
}

fn main() {
    let mut command: Vec<OsString> = env::args_os().skip(1).collect();
    assert!(!command.is_empty());
    let compiler = command.remove(0);
    let before = command.clone();
    let mode = env::var("MAYHEM_METADATA_MODE").expect("mode");
    assert!(mode == "passthrough" || mode == "published-target-metadata" || mode == "published-with-paths" || mode == "published-with-paths-relative");
    let is_target = command.windows(2).any(|w| w[0] == "--target" && w[1] == "sbpf-solana-solana");
    let is_compile = command.iter().any(|a| a == "--emit=dep-info,metadata,link" || a == "--emit=dep-info,link");
    let mut removed = 0;
    if mode != "passthrough" && is_target && is_compile {
        let crate_name = command.windows(2).find(|w| w[0] == "--crate-name").expect("crate name")[1].to_str().unwrap();
        let positions: Vec<usize> = command.iter().enumerate().filter(|(_, v)| v.to_str().unwrap().starts_with("metadata=")).map(|(i, _)| i).collect();
        assert_eq!(positions.len(), 1, "one metadata argument required");
        let position = positions[0];
        let old = command[position].to_str().unwrap().strip_prefix("metadata=").unwrap();
        let map = fs::read_to_string(env::var_os("MAYHEM_METADATA_MAP").expect("metadata map")).expect("read metadata map");
        let matched: Vec<Vec<&str>> = map.lines().map(|line| line.split('\t').collect()).filter(|parts: &Vec<&str>| parts.len() == 3 && parts[0] == old && parts[2] == crate_name).collect();
        assert_eq!(matched.len(), 1, "exactly one bound metadata mapping required");
        command[position] = OsString::from(format!("metadata={}", matched[0][1]));
        removed = 1;
    }
    if mode.starts_with("published-with-paths") && is_target && is_compile {
        let crate_name = command.windows(2).find(|w| w[0] == "--crate-name").unwrap()[1].to_str().unwrap().to_owned();
        let map = fs::read_to_string(env::var_os("MAYHEM_PATH_MAP").expect("path map")).expect("read path map");
        for line in map.lines() {
            let parts: Vec<&str> = line.split('\t').collect();
            assert_eq!(parts.len(), 3);
            if parts[0] == crate_name {
                command.push(OsString::from(format!("--remap-path-prefix={}={}", parts[1], parts[2])));
            }
        }
    }
    if mode == "published-with-paths-relative" && is_target && is_compile {
        let cwd = env::current_dir().expect("cwd");
        for value in command.iter_mut() {
            let text = value.to_str().expect("UTF-8 argument");
            if !text.starts_with('-') && text.ends_with(".rs") && PathBuf::from(text).is_absolute() {
                let source = PathBuf::from(text);
                let relative = source.strip_prefix(&cwd).expect("registry input is within crate cwd");
                *value = OsString::from(relative.to_str().expect("UTF-8 source").replace('\\', "/"));
            }
        }
    }
    if is_target && is_compile {
        let crate_name = command.windows(2).find(|w| w[0] == "--crate-name").unwrap()[1].to_str().unwrap().to_owned();
        if crate_name == "curve_accounts" {
            command.push(OsString::from("--extern"));
            command.push(OsString::from(format!("historical_anchor_program={}", env::var("MAYHEM_HISTORICAL_MACRO").unwrap())));
        }
        if crate_name == "curve_accounts" || crate_name == "mayhem_recovered" {
            command.push(OsString::from("-L"));
            command.push(OsString::from(format!("dependency={}", env::var("MAYHEM_HISTORICAL_DEPS").unwrap())));
        }
    }
    let path = PathBuf::from(env::var_os("MAYHEM_WRAPPER_RECORDS").expect("records"));
    let mut serial = 0_u32;
    let (mut file, record_id) = loop {
        let name = format!("{}-{}.json", process::id(), serial);
        match fs::OpenOptions::new().write(true).create_new(true).open(path.join(&name)) {
            Ok(file) => break (file, name),
            Err(error) if error.kind() == ErrorKind::AlreadyExists => serial += 1,
            Err(error) => panic!("create receipt: {error}"),
        }
    };
    let receipt = format!("{{\"record_id\":{},\"pid\":{},\"compiler\":{},\"cwd\":{},\"mode\":{},\"metadata_replaced\":{},\"before\":{},\"after\":{}}}\n",
        json(&record_id), process::id(), json(compiler.to_str().expect("compiler UTF-8")),
        json(env::current_dir().unwrap().to_str().expect("cwd UTF-8")), json(&mode), removed,
        array(&before), array(&command));
    file.write_all(receipt.as_bytes()).expect("write receipt");
    drop(file);
    let status = Command::new(compiler).args(command).status().expect("launch compiler");
    process::exit(status.code().unwrap_or(1));
}
