use std::{env, fs, process::{self, Command}, path::PathBuf};
use std::io::Write;

fn json(s: &str) -> String {
    let mut out = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""), '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"), '\r' => out.push_str("\\r"), '\t' => out.push_str("\\t"),
            c if c < '\u{20}' => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"'); out
}
fn array(xs: &[String]) -> String {
    format!("[{}]", xs.iter().map(|x| json(x)).collect::<Vec<_>>().join(","))
}
fn response_value(line: &str) -> String {
    assert!(line.starts_with('"') && line.ends_with('"') && line.len() >= 2, "noncanonical response line");
    let value = &line[1..line.len()-1];
    assert!(!value.contains('"') && !value.ends_with('\\') && !value.contains('\r') && !value.contains('\n'), "unsupported response escaping");
    value.to_string()
}
fn main() {
    let os_arguments: Vec<String> = env::args().skip(1).collect();
    let real = env::var("MAYHEM_LINKER_REAL").expect("real linker");
    let default = fs::read(env::var_os("MAYHEM_LINKER_DEFAULT").expect("default")).expect("default bytes");
    let script = env::var("MAYHEM_LINKER_SCRIPT").expect("script");
    let output = PathBuf::from(env::var_os("MAYHEM_LINKER_OUTPUT").expect("output"));
    fs::create_dir(&output).expect("fresh linker record directory");
    fs::write(output.join("os-arguments.json"), array(&os_arguments)).expect("OS argument record");
    let mut before = Vec::new();
    let mut response_count = 0;
    for value in &os_arguments {
        if let Some(path) = value.strip_prefix('@') {
            response_count += 1;
            assert_eq!(response_count, 1, "one response file supported");
            let data = fs::read(path).expect("response bytes");
            fs::write(output.join("response.bin"), &data).expect("response evidence");
            let text = String::from_utf8(data).expect("UTF-8 response");
            assert!(text.ends_with('\n'), "complete response file");
            before.extend(text.lines().map(response_value));
        } else { before.push(value.clone()); }
    }
    let mut after = before.clone();
    let mut changed = 0;
    let mut inputs = Vec::new();
    for (i, value) in before.iter().enumerate() {
        let script_path = if value == "-T" || value == "--script" {
            Some((before[i + 1].as_str(), i + 1, false))
        } else if let Some(path) = value.strip_prefix("--script=") {
            Some((path, i, true))
        } else { None };
        if let Some((path, index, equals)) = script_path {
            assert_eq!(fs::read(path).expect("incoming script"), default, "unexpected linker script");
            after[index] = if equals { format!("--script={script}") } else { script.clone() };
            changed += 1;
        }
        let path = value.strip_prefix("--version-script=").unwrap_or(value);
        let file = PathBuf::from(path);
        if file.is_file() && (path.ends_with(".o") || path.ends_with(".rlib") || value.starts_with("--version-script=")) {
            let retained = if path.ends_with(".o") || value.starts_with("--version-script=") {
                let name = format!("input-{i}.bin");
                fs::copy(&file, output.join(&name)).expect("retain ephemeral linker input"); name
            } else { String::new() };
            inputs.push(format!("{{\"argument\":{i},\"path\":{},\"retained\":{}}}", json(path), json(&retained)));
        }
    }
    assert_eq!(changed, 1, "exactly one script substitution");
    after.push(format!("-Map={}", output.join("link.map").display()));
    let receipt = format!("{{\"real\":{},\"cwd\":{},\"incoming\":{},\"forwarded\":{},\"inputs\":[{}]}}\n",
        json(&real), json(env::current_dir().unwrap().to_str().unwrap()), array(&before), array(&after), inputs.join(","));
    fs::OpenOptions::new().write(true).create_new(true).open(output.join("invocation.json")).expect("record")
        .write_all(receipt.as_bytes()).expect("write record");
    assert_eq!(&after[..2], ["-flavor", "gnu"]);
    let forwarded = after[2..].iter().map(|a| {
        let line = format!("\"{a}\"");
        assert_eq!(response_value(&line), *a);
        line + "\n"
    }).collect::<String>();
    let response = output.join("forwarded.rsp");
    fs::write(&response, forwarded).expect("forwarded response");
    let status = Command::new(real).args(["-flavor", "gnu"]).arg(format!("@{}", response.display())).status().expect("launch linker");
    let code = status.code().unwrap_or(1);
    fs::write(output.join("exit-code.txt"), format!("{code}\n")).expect("exit record");
    process::exit(code);
}
