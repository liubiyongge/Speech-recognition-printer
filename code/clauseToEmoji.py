import textToEmoji
import jieba

def clauseToEmoji(clause):
    words = list(jieba.cut(clause))
    for i in range(len(words)):
        words[i] = textToEmoji.textToEmoji(words[i])
    return "".join(words)