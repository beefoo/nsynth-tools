
def parseNumber(string, defaultValue=0):
    if isinstance(string, (int, float)):
        return string
    try:
        num = float(string)
        if "." not in string:
            num = int(string)
        return num
    except ValueError:
        return defaultValue

def filterResults(results, filters):
    if len(results) <= 0:
        return results

    sample = results[0]
    # Filter results
    for key, value in filters:
        sampleValue = sample[key]
        if value.startswith("<"):
            value = parseNumber(value[1:])
            results = [f for f in results if parseNumber(f[key]) < value]
        elif value.startswith(">"):
            value = parseNumber(value[1:])
            results = [f for f in results if parseNumber(f[key]) > value]
        elif isinstance(sampleValue, (list,)):
            results = [f for f in results if str(value) in [str(ff) for ff in f[key]]]
        else:
            results = [f for f in results if str(f[key])==str(value)]

    return results
