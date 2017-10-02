from re_pattern import reLu
text_and_error_number= [
    "всем привет", 0,
    "Не смотря на то, что превая буква не после точки, считаем это - текст без ошибок!", 0,
    "Text has capital letter without full stop before", 1,
    "text has more than 1 spaces  between words", 1,
    "text has more than 1 adjacent punctuation marks...", 1,
    "text has more than 1 punctuation marks between words, - this is not allowed", 1,
    "text has denied symbols $ ~ ^", None,
    "text has denied symbols $ ~ ^", None,
    ]



# def gen_el_in_dict_fun(opts, key_start_path, f_get_val):
#     """
#     Generator to traverse dict. Returns current key, and if value is dict
#      switches to keys of that last dict else on next call return value.
#      After traverse last dict returns to continue former dict.
#     :param opts:
#     :return: None
#     """
#     for k,v in opts.items():
#         yield k,v
#         if isinstance(v, dict):
#             if k == key:
#                 opts[k] = f_get_val(k)  # settable reference to value v #.setdefault()
#             yield from gen_el_in_dict_fun(v, key, f_get_val)
#         else:
#             yield v

for text, n_err in zip(text_and_error_number[::2], text_and_error_number[1::2]):

        n_replaces += 1
        values= {(level, 'r={}'.format(n_replaces)):{}} #load_page_elements_to_dict(task[level]) # {1:{},2:{},3:{}}
        m= cor.send(values)
    v_all.append((level, {k:v}))
print(d)