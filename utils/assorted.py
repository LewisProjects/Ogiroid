def renderBar(
    value: int,
    *,
    gap: int = 0,
    length: int = 32,
    point: str = "",
    fill: str = "-",
    empty: str = "-",
) -> str:
    # make the bar not wider than 32 even with gaps > 0
    length = int(length / int(gap + 1))

    # handles fill and empty's length
    fillLength = int(length * value / 100)
    emptyLength = length - fillLength

    # handles gaps
    gapFill = " " * gap if gap else ""

    return gapFill.join([fill] * (fillLength - len(point)) + [point] + [empty] * emptyLength)


def getPosition(num: int):
    pos_map = {1: "🥇", 2: "🥈", 3: "🥉", 0: "🏅"}
    if num in pos_map:
        return pos_map[num]
    else:
        return pos_map[0]
