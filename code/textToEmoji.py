import emoji_dict
import random
#支持中文转字符
def textToEmoji(text):
    myemoji = emoji_dict.emoji_ch.get(text)
    if myemoji == None:
        return text
    else:
        return myemoji[random.randint(0, len(myemoji) - 1 )]
