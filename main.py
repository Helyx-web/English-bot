import logging,sqlite3,random,os
from telegram import InlineKeyboardButton as BK, InlineKeyboardMarkup as MK
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from vocab_data import seed
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "PASTE_TOKEN_LU_SINI")
def db():
 c=sqlite3.connect('vocab.db');c.row_factory=sqlite3.Row;return c
  def m_kb():
 return MK([[BK("📚 Belajar Acak",callback_data="lrn")],[BK("📝 Quiz",callback_data="qz")]])
async def start(u,c):
 await u.message.reply_text("Pilih menu bos:",reply_markup=m_kb())
async def cb(u,c):
 q=u.callback_query;await q.answer();d=q.data
 if d=="menu":await q.edit_message_text("Pilih menu bos:",reply_markup=m_kb())
 elif d=="lrn":
  r=db().execute("SELECT * FROM vocabulary ORDER BY RANDOM() LIMIT 1").fetchone()
  t=f"📖 *{r['word']}* ({r['level']})\nArti: {r['meaning']}\nCara Baca: {r['pron']}\nContoh: _{r['example']}_\nArtinya: _{r['ex_m']}_"
    k=MK([[BK("➡️ Next Kata",callback_data="lrn")],[BK("🔙 Menu",callback_data="menu")]])
 await q.edit_message_text(t,reply_markup=k,parse_mode="Markdown")
elif d=="qz":
 v=db().execute("SELECT * FROM vocabulary ORDER BY RANDOM() LIMIT 4").fetchall()
 ans=v[0]['meaning'];opt=[x['meaning'] for x in v];random.shuffle(opt)
 t=f"Apa arti dari: *{v[0]['word']}* ?"
 k=[[BK(o,callback_data=f"ans_{'1' if o==ans else '0'}")] for o in opt]
 k.append([BK("🔙 Menu",callback_data="menu")])
 await q.edit_message_text(t,reply_markup=MK(k),parse_mode="Markdown")
elif d.startswith("ans_"):
 m="Bener Pinter Kau Anj 💯" if d.split("_")[1]=="1" else "Bego Amat Salah ☠️"
 await q.answer(m,show_alert=True)
async def init(app): seed()
def main():
 app=Application.builder().token(TOKEN).post_init(init).build()
 app.add_handler(CommandHandler("start",start))
 app.add_handler(CallbackQueryHandler(cb))
 app.run_polling()
if __name__=="__main__":main()
  
