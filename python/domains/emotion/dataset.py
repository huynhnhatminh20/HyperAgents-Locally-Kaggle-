# Emotion detection dataset — 5 classes: joy, anger, sadness, fear, surprise
# 20 train (e*) / 15 val (v*) / 15 test (x*)

DATASET = [
    # TRAIN
    {"id": "e01", "text": "I just got accepted into my dream university!", "label": "joy"},
    {"id": "e02", "text": "The whole team celebrated after winning the championship.", "label": "joy"},
    {"id": "e03", "text": "She ran to hug her father at the airport arrivals hall.", "label": "joy"},
    {"id": "e04", "text": "We finally finished the project and it turned out perfectly.", "label": "joy"},
    {"id": "e05", "text": "They promised a refund two weeks ago and still nothing.", "label": "anger"},
    {"id": "e06", "text": "He cut in line right in front of me without saying a word.", "label": "anger"},
    {"id": "e07", "text": "The landlord raised the rent without any prior notice.", "label": "anger"},
    {"id": "e08", "text": "She was blamed for a mistake she didn't make.", "label": "anger"},
    {"id": "e09", "text": "The old family dog passed away quietly in his sleep.", "label": "sadness"},
    {"id": "e10", "text": "He looked at the photos from when they were still together.", "label": "sadness"},
    {"id": "e11", "text": "The last letter from her father arrived a week after he died.", "label": "sadness"},
    {"id": "e12", "text": "She sat alone at the party, not knowing anyone there.", "label": "sadness"},
    {"id": "e13", "text": "The car skidded toward the railing on the icy bridge.", "label": "fear"},
    {"id": "e14", "text": "He lay awake listening to the unfamiliar sounds in the house.", "label": "fear"},
    {"id": "e15", "text": "The doctor asked her to come in as soon as possible.", "label": "fear"},
    {"id": "e16", "text": "The engine warning light turned on in the middle of the highway.", "label": "fear"},
    {"id": "e17", "text": "I had no idea they had been planning the party for months.", "label": "surprise"},
    {"id": "e18", "text": "The small startup was acquired for a billion dollars overnight.", "label": "surprise"},
    {"id": "e19", "text": "She opened the envelope and found a cheque for ten thousand dollars.", "label": "surprise"},
    {"id": "e20", "text": "He turned around and saw his childhood best friend standing there.", "label": "surprise"},
    # VAL
    {"id": "v01", "text": "The baby took her first steps today and everyone cheered.", "label": "joy"},
    {"id": "v02", "text": "He got the call saying his book would be published.", "label": "joy"},
    {"id": "v03", "text": "After years of trying, they finally had their first child.", "label": "joy"},
    {"id": "v04", "text": "The airline lost my luggage and offered me a $15 voucher.", "label": "anger"},
    {"id": "v05", "text": "They changed the policy without telling anyone affected.", "label": "anger"},
    {"id": "v06", "text": "He took credit for work that wasn't his.", "label": "anger"},
    {"id": "v07", "text": "She cleared out his room a month after the funeral.", "label": "sadness"},
    {"id": "v08", "text": "The town he grew up in was demolished to build a highway.", "label": "sadness"},
    {"id": "v09", "text": "The retirement home visit was the last time she saw him lucid.", "label": "sadness"},
    {"id": "v10", "text": "The trail disappeared and she realized she was completely lost.", "label": "fear"},
    {"id": "v11", "text": "He saw the brakes weren't responding as the hill got steeper.", "label": "fear"},
    {"id": "v12", "text": "The test results came back and the doctor went quiet.", "label": "fear"},
    {"id": "v13", "text": "The guest speaker turned out to be the CEO himself.", "label": "surprise"},
    {"id": "v14", "text": "She opened the attic and found letters she had never seen before.", "label": "surprise"},
    {"id": "v15", "text": "The last-place team beat the defending champions 5-0.", "label": "surprise"},
    # TEST
    {"id": "x01", "text": "The surgery was a success and he was cleared to go home.", "label": "joy"},
    {"id": "x02", "text": "Her painting won first place at the national competition.", "label": "joy"},
    {"id": "x03", "text": "They danced in the rain celebrating their engagement.", "label": "joy"},
    {"id": "x04", "text": "The contractor left the job half-done and stopped returning calls.", "label": "anger"},
    {"id": "x05", "text": "Her manager took her idea to the board without crediting her.", "label": "anger"},
    {"id": "x06", "text": "They were charged twice and customer service hung up on them.", "label": "anger"},
    {"id": "x07", "text": "The playground he played in as a child is now a parking lot.", "label": "sadness"},
    {"id": "x08", "text": "She re-read his last text message for the hundredth time.", "label": "sadness"},
    {"id": "x09", "text": "The flower he planted for her was still blooming years later.", "label": "sadness"},
    {"id": "x10", "text": "The lights went out and they heard a knock at the door.", "label": "fear"},
    {"id": "x11", "text": "He gripped the armrests as the plane dropped suddenly.", "label": "fear"},
    {"id": "x12", "text": "The scan showed something the doctor had not expected.", "label": "fear"},
    {"id": "x13", "text": "The quiet intern had written the algorithm that solved everything.", "label": "surprise"},
    {"id": "x14", "text": "She found out her neighbor was a famous novelist under a pen name.", "label": "surprise"},
    {"id": "x15", "text": "The investigation revealed the missing funds had been returned anonymously.", "label": "surprise"},
]

def get_split(split="train"):
    prefix_map = {"train": "e", "val": "v", "test": "x"}
    prefix = prefix_map.get(split, "e")
    return [d for d in DATASET if d["id"].startswith(prefix)]
