import hashlib
import hmac
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title='לומדת EEG', page_icon='🧠', layout='wide')
st.markdown('''<style>
.stApp {direction:rtl;background:#f5f7fb;color:#17263d}
[data-testid="stSidebar"] {background:#e8edf5;direction:rtl}
h1,h2,h3,p,label,.stMarkdown, [data-testid="stCaptionContainer"] {text-align:right}
.block-container {max-width:1150px;padding-top:2rem}
button {border-radius:10px!important} [data-testid="stImage"] {direction:ltr}
[data-testid="stMetric"] {background:white;border-radius:12px;padding:15px}
</style>''', unsafe_allow_html=True)

@st.cache_data
def load_course():
    return json.loads((ROOT/'course.json').read_text(encoding='utf-8'))

def figure(name, caption=None):
    st.image(str(ROOT/'assets'/f'{name}.png'), caption=caption, width='stretch')

def login():
    try:
        hashes = list(st.secrets.get('access', {}).get('code_hashes', []))
    except FileNotFoundError:
        hashes = []
    if not hashes:
        st.error('טרם הוגדרו קודי כניסה. יש להגדיר access.code_hashes ב־Secrets בהתאם לקובץ ההוראות.')
        st.stop()
    if st.session_state.get('authenticated'):
        return
    st.title('לומדת EEG למתמחים')
    st.write('מושגי יסוד → ערנות, נמנום ושינה • 83 דוגמאות • מבחן לכל פרק')
    with st.form('login'):
        code=st.text_input('קוד כניסה',type='password')
        submitted=st.form_submit_button('כניסה ללומדה',type='primary')
    if submitted:
        if time.time() < st.session_state.get('retry_after',0):
            st.error('נא להמתין לפני ניסיון נוסף.')
        else:
            digest=hashlib.sha256(code.encode()).hexdigest()
            if any(hmac.compare_digest(digest, str(x)) for x in hashes):
                st.session_state['authenticated']=True
                st.rerun()
            else:
                st.session_state['retry_after']=time.time()+3
                st.error('קוד הכניסה שגוי.')
    st.caption('ההתקדמות נשמרת במהלך החיבור בלבד. אין להזין מידע על מטופלים.')
    st.stop()

login()
course=load_course()
if st.session_state.get('course_version') != course['version']:
    for key in list(st.session_state):
        if key.startswith(('attempt_','answer_','page_')) or key in ('results','chapter_choice','mode_choice'):
            del st.session_state[key]
    st.session_state['course_version']=course['version']

def set_mode(mode):
    st.session_state['mode_choice']=mode

def move_page(chapter_id,index):
    st.session_state[f'page_{chapter_id}']=index

def open_chapter(chapter_id):
    st.session_state['chapter_choice']=chapter_id
    st.session_state['mode_choice']='לימוד'

with st.sidebar:
    st.title('🧠 לומדת EEG')
    st.caption('מהיסודות אל קריאת הרישום')
    chapter_id=st.selectbox('בחירת פרק',[c['id'] for c in course['chapters']],format_func=lambda x: next(f"פרק {x} · {c['title']}" for c in course['chapters'] if c['id']==x),key='chapter_choice')
    mode=st.radio('מסלול',['לימוד','כל הדוגמאות','מבחן','התוצאות שלי'],key='mode_choice')
    st.divider()
    st.caption('סדר הלימוד: תחילה מושגי יסוד (פרק 3), ואז קריאת מצבי ערנות ושינה (פרק 2).')
    if st.button('יציאה'):
        st.session_state.clear()
        st.rerun()

chapter=next(c for c in course['chapters'] if c['id']==chapter_id)
st.caption(f'קורס EEG / פרק {chapter_id}')
st.title(chapter['title'])
st.write(chapter['subtitle'])
st.session_state.setdefault('results',{})

if mode=='לימוד':
    pages=chapter['pages']
    idx=st.session_state.setdefault(f'page_{chapter_id}',0)
    idx=max(0,min(idx,len(pages)-1))
    st.caption(f'עמוד {idx+1} מתוך {len(pages)}')
    with st.expander('תוכן העניינים — מעבר ישיר לעמוד'):
        for i,p in enumerate(pages):
            st.button(f"{i+1}. {p['title']}",key=f'toc_{chapter_id}_{i}',on_click=move_page,args=(chapter_id,i),width='stretch')
    def navigation(position):
        prev,nxt=st.columns(2)
        with prev:
            st.button('→ העמוד הקודם',key=f'prev_{position}',disabled=idx==0,on_click=move_page,args=(chapter_id,idx-1),width='stretch')
        with nxt:
            if idx<len(pages)-1:
                st.button('העמוד הבא ←',key=f'next_{position}',type='primary',on_click=move_page,args=(chapter_id,idx+1),width='stretch')
            else:
                st.button('מעבר למבחן ←',key=f'exam_{position}',type='primary',on_click=set_mode,args=('מבחן',),width='stretch')
    navigation('top')
    item=pages[idx]
    with st.container(border=True):
        st.subheader(item['title'])
        st.markdown(item['text'])
    for example in item['examples']:
        with st.container(border=True):
            st.subheader(example['title'])
            figure(example['figure'],f"דוגמה {example['figure']} · אפשר ללחוץ על ההגדלה שבפינת התמונה")
            st.markdown(example['explanation'])
    if item.get('tip'): st.info(item['tip'])
    navigation('bottom')

elif mode=='כל הדוגמאות':
    examples=[(i,e) for i,p in enumerate(chapter['pages']) for e in p['examples']]
    st.subheader(f'{len(examples)} דוגמאות בפרק')
    query=st.text_input('חיפוש לפי נושא או מספר דוגמה',key=f'gallery_query_{chapter_id}')
    filtered=[(i,e) for i,e in examples if query.strip() in f"{e['figure']} {e['title']} {e['explanation']}" or not query.strip()]
    if not filtered:
        st.info('לא נמצאו דוגמאות מתאימות.')
    else:
        selected=st.selectbox('בחירת דוגמה',range(len(filtered)),format_func=lambda n:f"{filtered[n][1]['figure']} · {filtered[n][1]['title']}",key=f'gallery_{chapter_id}')
        i,example=filtered[selected]
        figure(example['figure'])
        st.subheader(example['title'])
        st.markdown(example['explanation'])
        def return_to_page():
            move_page(chapter_id,i)
            set_mode('לימוד')
        st.button('פתיחה בתוך רצף הלימוד',on_click=return_to_page)

elif mode=='מבחן':
    questions=[q for q in course['questions'] if q['chapter']==chapter_id]
    attempt_key=f'attempt_{chapter_id}'
    if attempt_key not in st.session_state:
        rng=random.Random()
        ordered=list(questions); rng.shuffle(ordered)
        order={q['id']:rng.sample(q['options'],len(q['options'])) for q in ordered}
        st.session_state[attempt_key]={'ids':[q['id'] for q in ordered],'options':order,'submitted':False,'answers':{}}
    attempt=st.session_state[attempt_key]
    ordered=[next(q for q in questions if q['id']==i) for i in attempt['ids']]
    if not attempt['submitted']:
        st.write('15 שאלות • תשובה אחת נכונה בכל שאלה • ציון באחוזים • אפשר לחזור לחומר לפני הגשה')
        with st.form(f'quiz_{chapter_id}'):
            answers={}
            for n,q in enumerate(ordered,1):
                st.subheader(f"{n}. {q['prompt']}")
                if q['figure']:
                    figure(q['figure'])
                answers[q['id']]=st.radio('בחירת תשובה',attempt['options'][q['id']],index=None,key=f"answer_{chapter_id}_{q['id']}",label_visibility='collapsed')
            submit=st.form_submit_button('הגשת המבחן',type='primary')
        if submit:
            missing=[str(i) for i,q in enumerate(ordered,1) if answers[q['id']] is None]
            if missing:
                st.error('יש לענות על כל השאלות. חסרות תשובות בשאלות: '+', '.join(missing))
            else:
                attempt.update(submitted=True,answers=answers)
                correct=sum(answers[q['id']]==q['answer'] for q in ordered)
                result={'chapter':chapter_id,'correct':correct,'total':len(ordered),'score':round(correct/len(ordered)*100),'submitted_at_utc':datetime.now(timezone.utc).isoformat(),'answers':[{'question':q['prompt'],'selected':answers[q['id']],'correct':q['answer'],'source':q['source']} for q in ordered]}
                st.session_state['results'].setdefault(chapter_id,[]).append(result)
                st.rerun()
    else:
        result=st.session_state['results'][chapter_id][-1]
        st.success(f"הוגש! הציון: {result['score']}% · {result['correct']} מתוך {result['total']}")
        st.download_button('הורדת התוצאה והמשוב (JSON)',json.dumps(result,ensure_ascii=False,indent=2),file_name=f'eeg_chapter_{chapter_id}_result.json',mime='application/json')
        for n,q in enumerate(ordered,1):
            selected=attempt['answers'][q['id']]
            with st.expander(f"{'✓' if selected==q['answer'] else '✗'} {n}. {q['prompt']}"):
                st.write('התשובה שלך: '+selected)
                st.write('התשובה הנכונה: '+q['answer'])
                st.write(q['explanation'])
                if q['figure']: st.caption('חזרה לדוגמה '+q['figure'])
                if q['figure']: figure(q['figure'],'איור '+q['figure'])
        if st.button('ניסיון חדש'):
            del st.session_state[attempt_key]
            for q in questions: st.session_state.pop(f"answer_{chapter_id}_{q['id']}",None)
            st.rerun()
        chapter_ids=[c['id'] for c in course['chapters']]
        chapter_index=chapter_ids.index(chapter_id)
        if chapter_index<len(chapter_ids)-1:
            st.button('המשך לפרק הבא ←',on_click=open_chapter,args=(chapter_ids[chapter_index+1],))
else:
    st.subheader('תוצאות המבחנים במהלך החיבור הנוכחי')
    for c in course['chapters']:
        st.write(f"**פרק {c['id']} · {c['title']}**")
        results=st.session_state['results'].get(c['id'],[])
        st.write(f"מבחנים שהוגשו: {len(results)}" + (f" · הציון הגבוה ביותר: {max(r['score'] for r in results)}%" if results else ''))
    st.caption('התוצאות נשמרות במהלך החיבור בלבד. ניתן להוריד כל תוצאה לאחר הגשת המבחן.')
