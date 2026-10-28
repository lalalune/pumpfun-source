#[path = "sell_accounting.rs"]
mod sell_accounting;
use std::io::{self, BufRead};
fn main() {
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let v: Vec<u64> = line.split(',').map(|s| s.parse().unwrap()).collect();
        match sell_accounting::sell_accounting(v[0], v[1], v[2], v[3]) {
            Ok(x) => println!("{},{},{},{},{}",x.protocol_fee,x.creator_fee,x.buyback_fee,x.user_output,x.retained_protocol_fee),
            Err(e) => println!("error:{}",e as u32),
        }
    }
}
