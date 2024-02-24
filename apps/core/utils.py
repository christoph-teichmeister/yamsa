def add_or_update_dict(dictionary: dict, update_value: dict):
    if not isinstance(update_value, dict):
        msg = "Non-dict values not handled yet"
        raise ValueError(msg)

    if isinstance(update_value, dict):
        for key, value in update_value.items():
            if dictionary.get(key) is None:
                dictionary[key] = value
            else:
                dictionary = add_or_update_dict(dictionary[key], value)

    return dictionary
