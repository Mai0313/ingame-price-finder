import re


def clean_game_name(name: str) -> str:
    cleaned_name = re.sub(r"[^\w\s]", "", name)
    cleaned_name = re.sub(r"\s+", "_", cleaned_name)
    return cleaned_name
