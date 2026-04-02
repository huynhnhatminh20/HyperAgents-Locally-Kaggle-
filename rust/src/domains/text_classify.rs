use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Sample {
    pub id: String,
    pub text: String,
    pub label: String,
}

pub fn all_samples() -> Vec<Sample> {
    vec![
        Sample { id: "t01".into(), text: "This movie was absolutely fantastic, I loved every minute!".into(), label: "positive".into() },
        Sample { id: "t02".into(), text: "Terrible service, would never come back again.".into(), label: "negative".into() },
        Sample { id: "t03".into(), text: "The weather today is cloudy with some sun.".into(), label: "neutral".into() },
        Sample { id: "t04".into(), text: "Best purchase I've ever made, highly recommend!".into(), label: "positive".into() },
        Sample { id: "t05".into(), text: "The food was disgusting and overpriced.".into(), label: "negative".into() },
        Sample { id: "t06".into(), text: "The meeting is scheduled for 3pm tomorrow.".into(), label: "neutral".into() },
        Sample { id: "t07".into(), text: "I'm so happy with the results, exceeded expectations!".into(), label: "positive".into() },
        Sample { id: "t08".into(), text: "Worst experience of my life, completely unacceptable.".into(), label: "negative".into() },
        Sample { id: "t09".into(), text: "The report contains data from Q3 2024.".into(), label: "neutral".into() },
        Sample { id: "t10".into(), text: "Amazing quality and the team was so helpful!".into(), label: "positive".into() },
        Sample { id: "t11".into(), text: "Broken on arrival, customer support was useless.".into(), label: "negative".into() },
        Sample { id: "t12".into(), text: "The building has three floors and a parking lot.".into(), label: "neutral".into() },
        Sample { id: "t13".into(), text: "This is exactly what I needed, perfect fit!".into(), label: "positive".into() },
        Sample { id: "t14".into(), text: "Completely waste of money, don't bother.".into(), label: "negative".into() },
        Sample { id: "t15".into(), text: "The train departs at 8:45 from platform 2.".into(), label: "neutral".into() },
        Sample { id: "t16".into(), text: "Outstanding performance, truly a masterpiece!".into(), label: "positive".into() },
        Sample { id: "t17".into(), text: "So disappointing, nothing like advertised.".into(), label: "negative".into() },
        Sample { id: "t18".into(), text: "The document is 15 pages long.".into(), label: "neutral".into() },
        Sample { id: "t19".into(), text: "What a delightful surprise, made my day!".into(), label: "positive".into() },
        Sample { id: "t20".into(), text: "Rude staff and dirty rooms. Avoid at all costs.".into(), label: "negative".into() },
        Sample { id: "v01".into(), text: "Incredible value for the price, super satisfied!".into(), label: "positive".into() },
        Sample { id: "v02".into(), text: "The product broke after just two days.".into(), label: "negative".into() },
        Sample { id: "v03".into(), text: "The conference will be held in Berlin this year.".into(), label: "neutral".into() },
        Sample { id: "v04".into(), text: "Loved the atmosphere and the friendly people!".into(), label: "positive".into() },
        Sample { id: "v05".into(), text: "Horrible quality, fell apart immediately.".into(), label: "negative".into() },
        Sample { id: "v06".into(), text: "Water boils at 100 degrees Celsius.".into(), label: "neutral".into() },
        Sample { id: "v07".into(), text: "Brilliant design, works like a charm!".into(), label: "positive".into() },
        Sample { id: "v08".into(), text: "Never again, the whole thing was a scam.".into(), label: "negative".into() },
        Sample { id: "v09".into(), text: "The file was uploaded on Monday morning.".into(), label: "neutral".into() },
        Sample { id: "v10".into(), text: "So grateful for this, it changed everything!".into(), label: "positive".into() },
        Sample { id: "v11".into(), text: "Appalling customer service, they hung up on me.".into(), label: "negative".into() },
        Sample { id: "v12".into(), text: "The library is open from 9am to 5pm.".into(), label: "neutral".into() },
        Sample { id: "v13".into(), text: "This exceeded all my expectations, wonderful!".into(), label: "positive".into() },
        Sample { id: "v14".into(), text: "Total disaster, nothing worked properly.".into(), label: "negative".into() },
        Sample { id: "v15".into(), text: "The population of the city is about 500,000.".into(), label: "neutral".into() },
        Sample { id: "x01".into(), text: "Phenomenal experience, would do it again in a heartbeat!".into(), label: "positive".into() },
        Sample { id: "x02".into(), text: "Utterly useless product, save your money.".into(), label: "negative".into() },
        Sample { id: "x03".into(), text: "The next bus arrives in 12 minutes.".into(), label: "neutral".into() },
        Sample { id: "x04".into(), text: "Just wow, this is the best thing ever!".into(), label: "positive".into() },
        Sample { id: "x05".into(), text: "Extremely frustrating, wasted hours trying to fix it.".into(), label: "negative".into() },
        Sample { id: "x06".into(), text: "The store is located on Main Street.".into(), label: "neutral".into() },
        Sample { id: "x07".into(), text: "Beautifully crafted and works perfectly!".into(), label: "positive".into() },
        Sample { id: "x08".into(), text: "Garbage quality, returned it immediately.".into(), label: "negative".into() },
        Sample { id: "x09".into(), text: "There are 24 hours in a day.".into(), label: "neutral".into() },
        Sample { id: "x10".into(), text: "I'm thrilled with this purchase, five stars!".into(), label: "positive".into() },
        Sample { id: "x11".into(), text: "Pathetic attempt, clearly no effort was made.".into(), label: "negative".into() },
        Sample { id: "x12".into(), text: "The meeting room seats up to 20 people.".into(), label: "neutral".into() },
        Sample { id: "x13".into(), text: "Superb quality, couldn't be happier!".into(), label: "positive".into() },
        Sample { id: "x14".into(), text: "Dreadful experience from start to finish.".into(), label: "negative".into() },
        Sample { id: "x15".into(), text: "The package weighs approximately 2 kilograms.".into(), label: "neutral".into() },
    ]
}

pub fn get_split(split: &str) -> Vec<Sample> {
    let prefix = if split.contains("val") { "v" } else if split.contains("test") { "x" } else { "t" };
    all_samples().into_iter().filter(|s| s.id.starts_with(prefix)).collect()
}

pub fn format_input(sample: &Sample) -> serde_json::Value {
    serde_json::json!({
        "domain": "text_classify",
        "text": sample.text,
        "id": sample.id,
        "instruction": "Classify the sentiment of the following text as exactly one of: positive, negative, or neutral. Respond with ONLY the label in lowercase.",
    })
}
