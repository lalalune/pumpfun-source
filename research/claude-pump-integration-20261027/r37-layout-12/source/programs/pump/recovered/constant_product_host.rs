#[path = "constant_product.rs"]
mod constant_product;
use std::io::{self, BufRead};
fn main() {
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let v: Vec<u128> = line.split(',').map(|s| s.parse().unwrap()).collect();
        match constant_product::constant_product_output(v[0], v[1], v[2]) {
            Ok(x) => println!("{x}"),
            Err(e) => println!("error:{}", e as u32),
        }
    }
}
