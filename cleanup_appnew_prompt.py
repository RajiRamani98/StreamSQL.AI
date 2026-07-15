from pathlib import Path
import re
p = Path('appnew.py')
text = p.read_text(encoding='utf-8')
start = text.find('#Streamlit app for fetching data:')
end = text.find('st.set_page_config(page_title="StreamSQL.AI",')
print('start', start, 'end', end)
if start != -1 and end != -1:
    new_text = text[:start] + text[end:]
    p.write_text(new_text, encoding='utf-8')
    print('removed legacy prompt block')
else:
    raise SystemExit('markers not found')
