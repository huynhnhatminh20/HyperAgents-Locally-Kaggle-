# Copyright (c) Meta Platforms, Inc. and affiliates.
# Built-in sentiment classification dataset for local testing.

DATASET = [
    # --- TRAIN (20 examples) ---
    {"id": "t01", "text": "This movie was absolutely fantastic, I loved every minute!", "label": "positive"},
    {"id": "t02", "text": "Terrible service, would never come back again.", "label": "negative"},
    {"id": "t03", "text": "The weather today is cloudy with some sun.", "label": "neutral"},
    {"id": "t04", "text": "Best purchase I've ever made, highly recommend!", "label": "positive"},
    {"id": "t05", "text": "The food was disgusting and overpriced.", "label": "negative"},
    {"id": "t06", "text": "The meeting is scheduled for 3pm tomorrow.", "label": "neutral"},
    {"id": "t07", "text": "I'm so happy with the results, exceeded expectations!", "label": "positive"},
    {"id": "t08", "text": "Worst experience of my life, completely unacceptable.", "label": "negative"},
    {"id": "t09", "text": "The report contains data from Q3 2024.", "label": "neutral"},
    {"id": "t10", "text": "Amazing quality and the team was so helpful!", "label": "positive"},
    {"id": "t11", "text": "Broken on arrival, customer support was useless.", "label": "negative"},
    {"id": "t12", "text": "The building has three floors and a parking lot.", "label": "neutral"},
    {"id": "t13", "text": "This is exactly what I needed, perfect fit!", "label": "positive"},
    {"id": "t14", "text": "Completely waste of money, don't bother.", "label": "negative"},
    {"id": "t15", "text": "The train departs at 8:45 from platform 2.", "label": "neutral"},
    {"id": "t16", "text": "Outstanding performance, truly a masterpiece!", "label": "positive"},
    {"id": "t17", "text": "So disappointing, nothing like advertised.", "label": "negative"},
    {"id": "t18", "text": "The document is 15 pages long.", "label": "neutral"},
    {"id": "t19", "text": "What a delightful surprise, made my day!", "label": "positive"},
    {"id": "t20", "text": "Rude staff and dirty rooms. Avoid at all costs.", "label": "negative"},

    # --- VAL (15 examples) ---
    {"id": "v01", "text": "Incredible value for the price, super satisfied!", "label": "positive"},
    {"id": "v02", "text": "The product broke after just two days.", "label": "negative"},
    {"id": "v03", "text": "The conference will be held in Berlin this year.", "label": "neutral"},
    {"id": "v04", "text": "Loved the atmosphere and the friendly people!", "label": "positive"},
    {"id": "v05", "text": "Horrible quality, fell apart immediately.", "label": "negative"},
    {"id": "v06", "text": "Water boils at 100 degrees Celsius.", "label": "neutral"},
    {"id": "v07", "text": "Brilliant design, works like a charm!", "label": "positive"},
    {"id": "v08", "text": "Never again, the whole thing was a scam.", "label": "negative"},
    {"id": "v09", "text": "The file was uploaded on Monday morning.", "label": "neutral"},
    {"id": "v10", "text": "So grateful for this, it changed everything!", "label": "positive"},
    {"id": "v11", "text": "Appalling customer service, they hung up on me.", "label": "negative"},
    {"id": "v12", "text": "The library is open from 9am to 5pm.", "label": "neutral"},
    {"id": "v13", "text": "This exceeded all my expectations, wonderful!", "label": "positive"},
    {"id": "v14", "text": "Total disaster, nothing worked properly.", "label": "negative"},
    {"id": "v15", "text": "The population of the city is about 500,000.", "label": "neutral"},

    # --- TEST (15 examples) ---
    {"id": "x01", "text": "Phenomenal experience, would do it again in a heartbeat!", "label": "positive"},
    {"id": "x02", "text": "Utterly useless product, save your money.", "label": "negative"},
    {"id": "x03", "text": "The next bus arrives in 12 minutes.", "label": "neutral"},
    {"id": "x04", "text": "Just wow, this is the best thing ever!", "label": "positive"},
    {"id": "x05", "text": "Extremely frustrating, wasted hours trying to fix it.", "label": "negative"},
    {"id": "x06", "text": "The store is located on Main Street.", "label": "neutral"},
    {"id": "x07", "text": "Beautifully crafted and works perfectly!", "label": "positive"},
    {"id": "x08", "text": "Garbage quality, returned it immediately.", "label": "negative"},
    {"id": "x09", "text": "There are 24 hours in a day.", "label": "neutral"},
    {"id": "x10", "text": "I'm thrilled with this purchase, five stars!", "label": "positive"},
    {"id": "x11", "text": "Pathetic attempt, clearly no effort was made.", "label": "negative"},
    {"id": "x12", "text": "The meeting room seats up to 20 people.", "label": "neutral"},
    {"id": "x13", "text": "Superb quality, couldn't be happier!", "label": "positive"},
    {"id": "x14", "text": "Dreadful experience from start to finish.", "label": "negative"},
    {"id": "x15", "text": "The package weighs approximately 2 kilograms.", "label": "neutral"},
]

def get_split(split="train"):
    """Get dataset split. split: 'train', 'val', or 'test'"""
    prefix_map = {"train": "t", "val": "v", "test": "x"}
    prefix = prefix_map.get(split, "t")
    return [d for d in DATASET if d["id"].startswith(prefix)]
