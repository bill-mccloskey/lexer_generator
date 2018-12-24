MACROS = {
    "ESC": r"\x1b",
    "CSI": r"\x1b\x5b",
    "params": r"{([0-9]*){;([0-9]*)}*}?",
}

RULES = [
    (r"\x07", "Bell"),
    (r"\x08", "Backspace"),
    (r"\x09", "Tab"),
    (r"\x0a|\x0b|\x0c", "LineFeed"),
    (r"\x0d", "CarriageReturn"),

    (r"{ESC}]([0-9]*);([^\x07]*)\x07", "OperatingSystemCommand"),
    (r"{CSI}{params}m", "ChangeCharacterAttributes"),
    (r"{CSI}{params}r", "SetScrollRegion"),
    (r"{CSI}{params}K", "EraseInLine"),
    (r"{CSI}{params}P", "EraseCharacters"),
]
