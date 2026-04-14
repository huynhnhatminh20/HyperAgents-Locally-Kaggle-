# Rust domain: classify code snippets as compiles / borrow_error / type_error
# 20 train + 15 val + 15 test = 50 examples

DATASET = [
    # ── TRAIN (t01-t20) ────────────────────────────────────────────────────────

    # compiles
    {"id": "t01", "label": "compiles", "code": """
fn main() {
    let x: i32 = 42;
    println!("{}", x);
}"""},
    {"id": "t02", "label": "compiles", "code": """
fn add(a: i32, b: i32) -> i32 {
    a + b
}
fn main() { println!("{}", add(2, 3)); }"""},
    {"id": "t03", "label": "compiles", "code": """
fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}
fn main() { println!("{}", greet("Rust")); }"""},
    {"id": "t04", "label": "compiles", "code": """
fn main() {
    let s = String::from("hello");
    let s2 = s.clone();
    println!("{} {}", s, s2);
}"""},
    {"id": "t05", "label": "compiles", "code": """
fn main() {
    let mut v = vec![1, 2, 3];
    v.push(4);
    println!("{:?}", v);
}"""},
    {"id": "t06", "label": "compiles", "code": """
fn largest(list: &[i32]) -> i32 {
    let mut max = list[0];
    for &item in list.iter() {
        if item > max { max = item; }
    }
    max
}
fn main() { println!("{}", largest(&[3, 1, 4, 1, 5])); }"""},
    {"id": "t07", "label": "compiles", "code": """
fn main() {
    let numbers = vec![1, 2, 3, 4, 5];
    let sum: i32 = numbers.iter().sum();
    println!("{}", sum);
}"""},

    # borrow_error
    {"id": "t08", "label": "borrow_error", "code": """
fn main() {
    let s = String::from("hello");
    let _s2 = s;          // s is moved here
    println!("{}", s);    // error: use of moved value
}"""},
    {"id": "t09", "label": "borrow_error", "code": """
fn main() {
    let mut v = vec![1, 2, 3];
    let r = &v;           // immutable borrow
    v.push(4);            // error: cannot borrow as mutable
    println!("{}", r[0]);
}"""},
    {"id": "t10", "label": "borrow_error", "code": """
fn takes_ownership(s: String) { println!("{}", s); }
fn main() {
    let s = String::from("hi");
    takes_ownership(s);
    takes_ownership(s);   // error: use of moved value
}"""},
    {"id": "t11", "label": "borrow_error", "code": """
fn main() {
    let mut x = 5;
    let r1 = &x;
    let r2 = &mut x;     // error: cannot borrow as mutable while borrowed
    println!("{} {}", r1, r2);
}"""},
    {"id": "t12", "label": "borrow_error", "code": """
fn main() {
    let s1 = String::from("hello");
    let s2 = s1;
    let s3 = s1;          // error: use of moved value
    println!("{}", s3);
}"""},

    # type_error
    {"id": "t13", "label": "type_error", "code": """
fn double(x: i32) -> i32 { x * 2 }
fn main() {
    let result = double("text"); // error: expected i32, found &str
    println!("{}", result);
}"""},
    {"id": "t14", "label": "type_error", "code": """
fn main() {
    let x: i32 = "hello"; // error: expected i32, found &str
    println!("{}", x);
}"""},
    {"id": "t15", "label": "type_error", "code": """
fn add(a: i32, b: i32) -> String {
    a + b  // error: expected String, found i32
}
fn main() { println!("{}", add(1, 2)); }"""},
    {"id": "t16", "label": "type_error", "code": """
fn main() {
    let v: Vec<i32> = vec![1, 2, 3];
    let s: String = v; // error: Vec<i32> cannot be converted to String
    println!("{}", s);
}"""},
    {"id": "t17", "label": "type_error", "code": """
struct Foo { x: i32 }
fn main() {
    let f = Foo { x: 1 };
    let sum = f + 1; // error: cannot add Foo and i32
    println!("{}", sum);
}"""},

    # more compiles (to balance)
    {"id": "t18", "label": "compiles", "code": """
fn main() {
    let pairs = vec![(1, 'a'), (2, 'b')];
    for (n, c) in &pairs {
        println!("{}: {}", n, c);
    }
}"""},
    {"id": "t19", "label": "compiles", "code": """
fn square(x: f64) -> f64 { x * x }
fn main() {
    let result = square(3.0);
    println!("{}", result);
}"""},
    {"id": "t20", "label": "compiles", "code": """
fn main() {
    let mut count = 0;
    for _ in 0..5 { count += 1; }
    println!("{}", count);
}"""},

    # ── VAL (v01-v15) ─────────────────────────────────────────────────────────

    # compiles
    {"id": "v01", "label": "compiles", "code": """
fn is_even(n: i32) -> bool { n % 2 == 0 }
fn main() { println!("{}", is_even(4)); }"""},
    {"id": "v02", "label": "compiles", "code": """
fn main() {
    let s = String::from("world");
    let len = s.len();
    println!("{} has {} chars", s, len);
}"""},
    {"id": "v03", "label": "compiles", "code": """
fn main() {
    let result: Result<i32, &str> = Ok(42);
    match result {
        Ok(v)  => println!("got {}", v),
        Err(e) => println!("err {}", e),
    }
}"""},
    {"id": "v04", "label": "compiles", "code": """
fn first(v: &[i32]) -> Option<&i32> { v.first() }
fn main() {
    let nums = vec![10, 20];
    println!("{:?}", first(&nums));
}"""},
    {"id": "v05", "label": "compiles", "code": """
fn main() {
    let mut map = std::collections::HashMap::new();
    map.insert("key", 1);
    println!("{:?}", map.get("key"));
}"""},

    # borrow_error
    {"id": "v06", "label": "borrow_error", "code": """
fn main() {
    let v = vec![1, 2, 3];
    let iter = v.iter();
    drop(v);             // error: cannot drop while borrowed by iter
    for x in iter { println!("{}", x); }
}"""},
    {"id": "v07", "label": "borrow_error", "code": """
fn main() {
    let mut s = String::from("hello");
    let r = &s;
    s.push_str(" world"); // error: cannot borrow as mutable while borrowed
    println!("{}", r);
}"""},
    {"id": "v08", "label": "borrow_error", "code": """
fn main() {
    let s1 = String::from("abc");
    let s2 = s1;
    println!("{}", s1); // error: use of moved value
}"""},
    {"id": "v09", "label": "borrow_error", "code": """
fn consume(s: String) { let _ = s; }
fn main() {
    let s = String::from("hi");
    consume(s);
    println!("{}", s); // error: borrow of moved value
}"""},
    {"id": "v10", "label": "borrow_error", "code": """
fn main() {
    let mut data = vec![1, 2, 3];
    let first = &data[0];
    data.clear();        // error: cannot borrow as mutable
    println!("{}", first);
}"""},

    # type_error
    {"id": "v11", "label": "type_error", "code": """
fn main() {
    let x: u32 = -1; // error: negative value for unsigned type
    println!("{}", x);
}"""},
    {"id": "v12", "label": "type_error", "code": """
fn main() {
    let a: f64 = 1.5;
    let b: i32 = 2;
    let c = a + b; // error: cannot add f64 and i32
    println!("{}", c);
}"""},
    {"id": "v13", "label": "type_error", "code": """
fn greet(name: String) { println!("Hello, {}", name); }
fn main() {
    greet(42); // error: expected String, found integer
}"""},
    {"id": "v14", "label": "type_error", "code": """
struct Point { x: i32, y: i32 }
fn main() {
    let p = Point { x: 1, y: 2 };
    println!("{}", p); // error: Point does not implement Display
}"""},
    {"id": "v15", "label": "type_error", "code": """
fn main() {
    let nums: Vec<i32> = vec![1, 2, 3];
    let total: i32 = nums.iter().product::<f64>() as i32; // iter yields &i32, product::<f64> wrong
    println!("{}", total);
}"""},

    # ── TEST (x01-x15) ────────────────────────────────────────────────────────

    # compiles
    {"id": "x01", "label": "compiles", "code": """
fn factorial(n: u64) -> u64 {
    if n == 0 { 1 } else { n * factorial(n - 1) }
}
fn main() { println!("{}", factorial(5)); }"""},
    {"id": "x02", "label": "compiles", "code": """
fn main() {
    let words = vec!["rust", "is", "great"];
    let sentence = words.join(" ");
    println!("{}", sentence);
}"""},
    {"id": "x03", "label": "compiles", "code": """
fn main() {
    let opt: Option<i32> = Some(7);
    if let Some(v) = opt {
        println!("value: {}", v);
    }
}"""},
    {"id": "x04", "label": "compiles", "code": """
fn max_of(a: i32, b: i32) -> i32 {
    if a > b { a } else { b }
}
fn main() { println!("{}", max_of(10, 20)); }"""},
    {"id": "x05", "label": "compiles", "code": """
fn main() {
    let evens: Vec<i32> = (1..=10).filter(|x| x % 2 == 0).collect();
    println!("{:?}", evens);
}"""},

    # borrow_error
    {"id": "x06", "label": "borrow_error", "code": """
fn main() {
    let s = String::from("hello");
    let r1 = &s;
    let r2 = &s;
    let r3 = &mut s; // error: cannot borrow as mutable, already borrowed as immutable (and s is not mut)
    println!("{} {} {}", r1, r2, r3);
}"""},
    {"id": "x07", "label": "borrow_error", "code": """
fn main() {
    let x = vec![1, 2, 3];
    let y = x;
    println!("{:?}", x); // error: use of moved value
}"""},
    {"id": "x08", "label": "borrow_error", "code": """
fn push(v: &Vec<i32>, item: i32) { /* pretend */ }
fn main() {
    let mut v = vec![1];
    let r = &v;
    push(&mut v, 2); // error: cannot borrow as mutable (immutable ref r active)
    println!("{}", r[0]);
}"""},
    {"id": "x09", "label": "borrow_error", "code": """
fn main() {
    let mut v = vec![1, 2, 3];
    for x in &v {
        v.push(*x * 2); // error: cannot borrow as mutable while borrowed
    }
}"""},
    {"id": "x10", "label": "borrow_error", "code": """
fn print_it(s: String) { println!("{}", s); }
fn main() {
    let msg = String::from("hi");
    print_it(msg);
    println!("{}", msg); // error: use of moved value
}"""},

    # type_error
    {"id": "x11", "label": "type_error", "code": """
fn negate(b: bool) -> bool { !b }
fn main() {
    println!("{}", negate(1)); // error: expected bool, found integer
}"""},
    {"id": "x12", "label": "type_error", "code": """
fn main() {
    let x: &str = String::from("hello"); // error: type mismatch (String vs &str)
    println!("{}", x);
}"""},
    {"id": "x13", "label": "type_error", "code": """
fn sum_slice(s: &[i32]) -> i32 { s.iter().sum() }
fn main() {
    let total = sum_slice(42); // error: expected &[i32], found integer
    println!("{}", total);
}"""},
    {"id": "x14", "label": "type_error", "code": """
fn main() {
    let v: Vec<i32> = vec![1, 2, 3];
    let doubled: Vec<i32> = v.iter().map(|x| x as f64).collect(); // error: f64 != i32
    println!("{:?}", doubled);
}"""},
    {"id": "x15", "label": "type_error", "code": """
fn main() {
    let result: i32 = if true { 1 } else { "one" }; // error: mismatched types in if/else
    println!("{}", result);
}"""},
]


def get_split(split="train"):
    """Return train / val / test split."""
    prefix_map = {"train": "t", "val": "v", "test": "x"}
    prefix = prefix_map.get(split, "t")
    return [d for d in DATASET if d["id"].startswith(prefix)]
