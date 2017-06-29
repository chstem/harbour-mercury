function capitalize(s)
{
    return s && s[0].toUpperCase() + s.slice(1);
}

function get_initials(str) {
    var res = str.split(" ")
    var initials = res[0][0]
    if (res.length > 1) initials += res[res.length-1][0]
    return initials.toUpperCase()
}

