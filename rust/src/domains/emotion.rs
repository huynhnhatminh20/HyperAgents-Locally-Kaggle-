use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Sample {
    pub id: String,
    pub text: String,
    pub label: String,
}

pub fn all_samples() -> Vec<Sample> {
    vec![
        // TRAIN (e*)
        Sample { id: "e01".into(), text: "I just got accepted into my dream university!".into(), label: "joy".into() },
        Sample { id: "e02".into(), text: "The whole team celebrated after winning the championship.".into(), label: "joy".into() },
        Sample { id: "e03".into(), text: "She ran to hug her father at the airport arrivals hall.".into(), label: "joy".into() },
        Sample { id: "e04".into(), text: "We finally finished the project and it turned out perfectly.".into(), label: "joy".into() },
        Sample { id: "e05".into(), text: "They promised a refund two weeks ago and still nothing.".into(), label: "anger".into() },
        Sample { id: "e06".into(), text: "He cut in line right in front of me without saying a word.".into(), label: "anger".into() },
        Sample { id: "e07".into(), text: "The landlord raised the rent without any prior notice.".into(), label: "anger".into() },
        Sample { id: "e08".into(), text: "She was blamed for a mistake she didn't make.".into(), label: "anger".into() },
        Sample { id: "e09".into(), text: "The old family dog passed away quietly in his sleep.".into(), label: "sadness".into() },
        Sample { id: "e10".into(), text: "He looked at the photos from when they were still together.".into(), label: "sadness".into() },
        Sample { id: "e11".into(), text: "The last letter from her father arrived a week after he died.".into(), label: "sadness".into() },
        Sample { id: "e12".into(), text: "She sat alone at the party, not knowing anyone there.".into(), label: "sadness".into() },
        Sample { id: "e13".into(), text: "The car skidded toward the railing on the icy bridge.".into(), label: "fear".into() },
        Sample { id: "e14".into(), text: "He lay awake listening to the unfamiliar sounds in the house.".into(), label: "fear".into() },
        Sample { id: "e15".into(), text: "The doctor asked her to come in as soon as possible.".into(), label: "fear".into() },
        Sample { id: "e16".into(), text: "The engine warning light turned on in the middle of the highway.".into(), label: "fear".into() },
        Sample { id: "e17".into(), text: "I had no idea they had been planning the party for months.".into(), label: "surprise".into() },
        Sample { id: "e18".into(), text: "The small startup was acquired for a billion dollars overnight.".into(), label: "surprise".into() },
        Sample { id: "e19".into(), text: "She opened the envelope and found a cheque for ten thousand dollars.".into(), label: "surprise".into() },
        Sample { id: "e20".into(), text: "He turned around and saw his childhood best friend standing there.".into(), label: "surprise".into() },
        // VAL (v*)
        Sample { id: "v01".into(), text: "The baby took her first steps today and everyone cheered.".into(), label: "joy".into() },
        Sample { id: "v02".into(), text: "He got the call saying his book would be published.".into(), label: "joy".into() },
        Sample { id: "v03".into(), text: "After years of trying, they finally had their first child.".into(), label: "joy".into() },
        Sample { id: "v04".into(), text: "The airline lost my luggage and offered me a $15 voucher.".into(), label: "anger".into() },
        Sample { id: "v05".into(), text: "They changed the policy without telling anyone affected.".into(), label: "anger".into() },
        Sample { id: "v06".into(), text: "He took credit for work that wasn't his.".into(), label: "anger".into() },
        Sample { id: "v07".into(), text: "She cleared out his room a month after the funeral.".into(), label: "sadness".into() },
        Sample { id: "v08".into(), text: "The town he grew up in was demolished to build a highway.".into(), label: "sadness".into() },
        Sample { id: "v09".into(), text: "The retirement home visit was the last time she saw him lucid.".into(), label: "sadness".into() },
        Sample { id: "v10".into(), text: "The trail disappeared and she realized she was completely lost.".into(), label: "fear".into() },
        Sample { id: "v11".into(), text: "He saw the brakes weren't responding as the hill got steeper.".into(), label: "fear".into() },
        Sample { id: "v12".into(), text: "The test results came back and the doctor went quiet.".into(), label: "fear".into() },
        Sample { id: "v13".into(), text: "The guest speaker turned out to be the CEO himself.".into(), label: "surprise".into() },
        Sample { id: "v14".into(), text: "She opened the attic and found letters she had never seen before.".into(), label: "surprise".into() },
        Sample { id: "v15".into(), text: "The last-place team beat the defending champions 5-0.".into(), label: "surprise".into() },
        // TEST (x*)
        Sample { id: "x01".into(), text: "The surgery was a success and he was cleared to go home.".into(), label: "joy".into() },
        Sample { id: "x02".into(), text: "Her painting won first place at the national competition.".into(), label: "joy".into() },
        Sample { id: "x03".into(), text: "They danced in the rain celebrating their engagement.".into(), label: "joy".into() },
        Sample { id: "x04".into(), text: "The contractor left the job half-done and stopped returning calls.".into(), label: "anger".into() },
        Sample { id: "x05".into(), text: "Her manager took her idea to the board without crediting her.".into(), label: "anger".into() },
        Sample { id: "x06".into(), text: "They were charged twice and customer service hung up on them.".into(), label: "anger".into() },
        Sample { id: "x07".into(), text: "The playground he played in as a child is now a parking lot.".into(), label: "sadness".into() },
        Sample { id: "x08".into(), text: "She re-read his last text message for the hundredth time.".into(), label: "sadness".into() },
        Sample { id: "x09".into(), text: "The flower he planted for her was still blooming years later.".into(), label: "sadness".into() },
        Sample { id: "x10".into(), text: "The lights went out and they heard a knock at the door.".into(), label: "fear".into() },
        Sample { id: "x11".into(), text: "He gripped the armrests as the plane dropped suddenly.".into(), label: "fear".into() },
        Sample { id: "x12".into(), text: "The scan showed something the doctor had not expected.".into(), label: "fear".into() },
        Sample { id: "x13".into(), text: "The quiet intern had written the algorithm that solved everything.".into(), label: "surprise".into() },
        Sample { id: "x14".into(), text: "She found out her neighbor was a famous novelist under a pen name.".into(), label: "surprise".into() },
        Sample { id: "x15".into(), text: "The investigation revealed the missing funds had been returned anonymously.".into(), label: "surprise".into() },
    ]
}

pub fn get_split(split: &str) -> Vec<Sample> {
    let prefix = if split.contains("val") { "v" } else if split.contains("test") { "x" } else { "e" };
    all_samples().into_iter().filter(|s| s.id.starts_with(prefix)).collect()
}

pub fn format_input(sample: &Sample) -> serde_json::Value {
    serde_json::json!({
        "domain": "emotion",
        "text": sample.text,
        "id": sample.id,
        "instruction": "Detect the primary emotion expressed in the following text. Choose exactly one of: joy, anger, sadness, fear, surprise. Respond with ONLY the emotion label in lowercase.",
    })
}
