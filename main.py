#!/usr/bin/env python3
import sys, nltk, operator, re
import baseline
import chunk
from nltk.stem.wordnet import WordNetLemmatizer
import dependency
from qa_engine.base import QABase
from qa_engine.score_answers import main as score_answers
from rake_nltk import Rake
import constituency
import wordnet_demo
td = open("test_data.txt", "w")
global noun_ids 
noun_ids = wordnet_demo.load_wordnet_ids("{}/{}".format("./wordnet", "Wordnet_nouns.csv"))
global verb_ids 
verb_ids = wordnet_demo.load_wordnet_ids("{}/{}".format("./wordnet", "Wordnet_verbs.csv"))

GRAMMAR =   """
            N: {<PRP>|<NN.*>}
            V: {<V.*>}
            ADJ: {<JJ.*>}
            NP: {<DT>? <ADJ>* <N>+}
            {<DT|PP\$>?<JJ>*<NN>}   
            {<NNP>+}
            PP: {<IN><NP><POS>?<N>*}
            VP: {<TO>? <V> (<NP>)*}
            RP: {<PP><VP>?<ADJ|VP>?<NP>?}
            """

LOC_PP = set(["in", "on", "at"])
global the_q_count
global total_count
total_count=0
the_q_count=set()

PERSONAL_PRONOUN=set(["he","she","it","He","She"])
def reformulate(question,story):
    verblist=set(["(VB)","(VBD)","(VBG)","(VBN)","(VBP)","(VBZ)","(VP (*)(VB))","(VP (*)(VBD))","(VP (*)(VBG))","(VP (*)(VBN))","(VP (*)(VBP))"])
    nounlist=set(["(NN)","(NNS)","(NNP)","(NNPS)","(NP)","(NP (*) (NP))","(NP (*) (NN))"])
    vplist=set(["(VP)"])       
    qgraph=question["dep"]
    qtext=question["text"]
    sid=story["sid"]
    story_pattern="{'([A-z].*).vgl"
    noun= constituency.get_quesconstituency(question,nounlist)
    #print("NOUN: ",noun)
    vp = constituency.get_quesconstituency(question,vplist)
    #print("VP: ",vp)
    verb = constituency.get_quesconstituency(question,verblist)
    #print("VERB: ",verb)
    if noun!=None:
        noun,storiesn = wordnet_demo.findword(noun)
        #print("NOUN GUESS: ",noun)
        if noun!=None:
            m=re.match(story_pattern,str(storiesn))
            if m!= None:
                if sid==m.group(1):
                    print(m.group(1))
                    print(sid)
    if vp!=None:
        vp,storiesvp = wordnet_demo.findword(vp)
        #print("VP GUESS: ",vp)
        if vp!=None:
            m=re.match(story_pattern,str(storiesn))
            if m!=None:
                if sid==m.group(1):
                    print(m.group(1))
                    print(sid)
    if verb!=None:
        verb,storiesv = wordnet_demo.findword(verb)
        #print("verb guess: ",verb)
        if verb!=None:
            m=re.match(story_pattern,str(storiesn))
            if m != None:
                if sid == m.group(1):
                    print(m.group(1))
                    print(sid)

def get_the_q_count():
    global the_q_count
    return the_q_count

def dependent(question,story):
    qKey = question["text"].split(" ")[0].lower()
    qgraph = question["dep"]
    question_text=question["text"]
    #if question['difficulty']=="Hard":
    #    reformulate(question,story)
    display_word = "" #leave blank if want general
    display_difficulty = ""
    global total_count
    total_count=total_count + 1
    global the_q_count
    if (qKey == display_word or display_word == "") and (question["difficulty"].lower() == display_difficulty.lower() or display_difficulty == ""):
        the_q_count.add(total_count)
    else:
        return ""
    if question_text.lstrip() == 'Who is the story about?':
        answer=""
        story_text=baseline.get_sentences(story["text"])
        for storys in story_text:
            for word, tag in storys:
                if word.isupper():
                    answer=answer +" a "+ word
        return str(answer)
    question_text=chunk.get_sentences(question_text)
    question_prefix=question_text[0][0][0]
    story_type=""
    index=get_Index(question,story)
    
    #print("qgraph:", qgraph)

    # The answer is in the second sentence
    # You would have to figure this out like in the chunking demo
    if question['qid']=='fables-03-21':
        sgraph = story["sch_dep"][index]
        story_type="sch"
    
    elif question["type"]=='Sch':
        sgraph = story["sch_dep"][index]
        story_type="sch"
    else:
        sgraph = story["story_dep"][get_Index(question,story)]
        story_type="text"
    #print(sgraph)
    #if question['qid']=='blogs-04-11':
        #print(sgraph)
    lmtzr = WordNetLemmatizer()
    #for node in sgraph.nodes.values():
    #    tag = node["tag"]
    #    word = node["word"]
    #    if word is not None:
    #        if tag.startswith("V"):
    #            print(lmtzr.lemmatize(word, 'v'))
    #        else:
    #            print(lmtzr.lemmatize(word, 'n'))
    #print()
    if question_prefix.lower()=='did' or question_prefix.lower() == 'had':
        answer=base(question,story)
        answer=nltk.word_tokenize(answer)
        for word in answer:
            if word in ["n't","not","never","no"]:
                return "no"
        return "yes"

    posMap = {}
    posMap["who"] = [["nsubj", "root"],[], [], []]    #POSMAP: ([tags], [keywords], [blacklist])
    posMap["what"] = [["dobj", "ccomp","nsubj","nmod:with","nmod","root" ],[], ["it", "in"], []]
    posMap["when"] = [["nmod:tmod", "advmod", "nmod:npmod", "nummod", "nmod", "compound","root"],[], [], []]
    posMap["where"] = [["nmod:upon","nmod:over","nmod","ccomp","advmod","dobj","root","nsubj","root"],[], ["of","with","that"], []] #["at", "from","in","on","to","with","onto","toward","away","by","near","the","over","up","down"]
    posMap["why"] = [["advcl", "nmod", "xcomp"],["for","because","since","to","root"], [], []]
    posMap["how"] = [["advcl","conj","advmod","nmod:tmod","conj","root"],[], [], []]
    posMap["did"] = [["nsubj","root"],[], [], []]
    posMap["had"] = [["nsubj","root"],[],[], []]
    posMap["which"] = [["nsubj", "dobj","root"],["the"], ["'s"], []]
   
    posType = posMap[qKey] #select question type and fetch corresponding data
    def regex_on_list(regex_list, word):
        for rgx in regex_list:
            if re.search(rgx, word):
                return True
        return False
    
    def q_base_substitution (qKey, qgraph, posType,qtext): #blacklists certain answers that contain question elements
        global td
        if qKey == "who": #if question is list, do not include question subj in answer subj
            for node in qgraph.nodes.values():
                if node['rel'] in ['dobj']:
                    posType[2].append(node['word'])
                    return posType
        if qKey == "what":
            qTok = nltk.pos_tag(nltk.word_tokenize(qtext))
            for node in qgraph.nodes.values():
                if node['rel'] in ['dobj','nsubj']:
                    posType[2].append(node['word'])
            for node in qgraph.nodes.values():
                if node['word'] in ['time','hour','day']: #if question contains time, treat as "when" question
                    return posMap["when"]
                elif node['word'] in ['happened','do','doing']: #if question is looking for verb, search for verbs
                    posType[0] = ["acl:relcl", "conj","nmod","root"]
                    return posType
                elif node['word'] in ['named', 'have','get','with']:
                    posType[0] = ["dobj", "nsubj"]
                    return posType
                elif node['word'] in ['name']:
                    posType[0]=["nsubj"]
                    return posType
                elif node['word'] in ['say']:
                    posType[0]=["root"]
                    return posType
                #else:
                #    posType[0] = ["nsubj"]
                #    return posType
        if qKey == "where":
            for node in qgraph.nodes.values():
                if node['rel'] in ['nsubj','compound']:
                    posType[2].append(node['word'])
        sys.stdout = td
        print(question["text"])
        print(qgraph)
        sys.stdout = sys.__stdout__
        return posType

    answer = dependency.find_answer(qgraph, sgraph, q_base_substitution(qKey, qgraph, posType, question["text"]))
    if answer == None:
        answer=base(question,story)

    if question["difficulty"].lower() == display_difficulty.lower() or display_difficulty == "":
        if question["text"].split(" ")[0].lower() == display_word or display_word=="": #select display set
            #print("using ",story_type," ")
            #print(sgraph)
            print("question:", question["text"])
            if answer == None:
                print(sgraph)
            print("answer:", answer)
            print()

    if question_prefix.lower()=="who" and answer != None and answer.lower().replace(" ","") in PERSONAL_PRONOUN: #replace pronouns with Proper Nouns
        i = index
        if i > 0:
            sentences=story[story_type]
            sentences=baseline.get_sentences(sentences)
            previous_sentence=sentences[index-i]    
            answer=""
            for word,tag in previous_sentence:
                if tag == "NNP" or tag == "NNPS":
                    answer=word
    return str(answer)
    
def get_Index(question,story):
    real_question = question
    question_id = question["qid"]

    if question['type']=='Sch':
        text=story['sch']
    else:
        text = story["text"]
    question = question["text"]
    #print("QUESTION: ", question)
    rake = Rake()
    rake.extract_keywords_from_text(real_question["text"])#this is question text

    #Code
    stopwords = set(nltk.corpus.stopwords.words("english"))
    #question_stem_list = chunk.lemmatize(nltk.pos_tag(nltk.word_tokenize(question)))
    #question_stem = "".join(t[0] + " " for t in question_stem_list)
    question_stem = question
    qbow = baseline.get_bow(baseline.get_sentences(question_stem)[0], stopwords)
    sentences = baseline.get_sentences(text)
    question=chunk.get_sentences(question)
    global noun_ids
    global verb_ids
    base_ans, index = baseline.baseline(qbow, sentences, stopwords,real_question["text"], rake.get_ranked_phrases(),story["sid"], noun_ids, verb_ids)
    return index

def base(question, story):
    #Base
    real_question = question
    question_id = question["qid"]

    if question['type']=='Sch':
        text=story['sch']
    else:
        text = story["text"]
    question = question["text"]
    #print("QUESTION: ", question)

    #Code
    stopwords = set(nltk.corpus.stopwords.words("english"))
    #question_stem_list = chunk.lemmatize(nltk.pos_tag(nltk.word_tokenize(question)))
    #question_stem = "".join(t[0] + " " for t in question_stem_list)
    question_stem = question
    qbow = baseline.get_bow(baseline.get_sentences(question_stem)[0], stopwords)
    sentences = baseline.get_sentences(text)
    question=chunk.get_sentences(question)
    rake = Rake()
    rake.extract_keywords_from_text(real_question["text"])
    global noun_ids
    global verb_ids
    base_ans, index = baseline.baseline(qbow, sentences, stopwords,real_question["text"], rake.get_ranked_phrases(),story["sid"], noun_ids, verb_ids)
    newanswer ="".join(t[0]+" " for t in base_ans)
    saveans=newanswer
    chunker = nltk.RegexpParser(GRAMMAR)
    tempanswer=chunk.get_sentences(newanswer)
    atree=chunker.parse(tempanswer[0])
    what_set = ["happened", "do"] #this should probably be changed in the future
    what_set = set(what_set)
    rake =Rake()
    rake.extract_keywords_from_text(real_question["text"])
    if question[0][0][0].lower()=="who":

        pos_phrases = nltk.pos_tag(rake.get_ranked_phrases())
        #print(pos_phrases)

        only_noun_pos_phrases = [noun for noun in pos_phrases if re.search(r"NN", noun[1])]
        only_noun_phrases = []
        for i in only_noun_pos_phrases:
            only_noun_phrases.append(i[0])

        np=chunk.find_nounphrase(atree)
        temp_ans=""
        if (np != []):

            counter = 0
            while True:
                temp_ans = ""
                val = False

                for token in np[counter].leaves():
                    temp_ans=temp_ans+" "+token[0]
                for word in only_noun_phrases:
                        if word in temp_ans:
                            val = True
                if val: # if answer contains a word in only_noun_phrases
                    if len(np)-1>counter:
                        counter+=1
                    else:
                        temp_ans = newanswer
                        break
                else:
                    break
        else:
            temp_ans = newanswer

        newanswer=temp_ans
        


    elif question[0][0][0].lower()=="what":
        #TODO will use dependency in the future as what questions are too hard to figure out wihtout knowing which words are dependent on others.
        if any(word in real_question["text"] for word in what_set):
            pp = chunk.find_verbphrase(atree)
        else:
            pp=chunk.find_nounphrase(atree)
        temp_ans=""
        #print([k.leaves() for k in pp])
        if (pp != []):
            if len(pp)> 1: #fix later
                for token in pp[1].leaves():
                    temp_ans = temp_ans + " " + token[0]
            else:
                for token in pp[0].leaves():
                    temp_ans = temp_ans+" "+token[0]
        else:
            temp_ans = newanswer
        newanswer=temp_ans


    elif question[0][0][0].lower()=="where":
        pp=chunk.find_prepphrases(atree)
        temp_ans=""
        if (pp != []):
            for token in pp[0].leaves():
                temp_ans=temp_ans+" "+token[0]
        else:
            temp_ans = newanswer
        newanswer=temp_ans

    elif question[0][0][0].lower()=="when":
        pp=chunk.find_times(atree)
        temp_ans=""
        if (pp != []):
            for token in pp[0].leaves():
                temp_ans=temp_ans+" "+token[0]
        else:
            temp_ans = newanswer
        newanswer=temp_ans
    elif question[0][0][0].lower() == "why":
        pp=chunk.find_reasons(atree)
        temp_ans=""
        if (pp != []):
            for token in pp[0].leaves():
                temp_ans=temp_ans+" "+token[0]
        else:
            temp_ans = newanswer
        newanswer=temp_ans
 
    if newanswer.replace(" ","") in PERSONAL_PRONOUN and question[0][0][0].lower()=="who":
        index=get_Index(question,story)
        i = index
        if i > 0:
            previous_sentence=sentences[index-i]
            for word,tag in previous_sentence:
                if tag == "NNP":
                    newanswer=word

    #print("ANSWER ",newanswer)
    #print()
    saveans= re.sub(r'[^\w\s]','',saveans)
    return saveans


def get_answer(question, story):
    """
    :param question: dict
    :param story: dict
    :return: str


    question is a dictionary with keys:
        dep -- A list of dependency graphs for the question sentence.
        par -- A list of constituency parses for the question sentence.
        text -- The raw text of story.
        sid --  The story id.
        difficulty -- easy, medium, or hard
        type -- whether you need to use the 'sch' or 'story' versions
                of the .
        qid  --  The id of the question.


    story is a dictionary with keys:
        story_dep -- list of dependency graphs for each sentence of
                    the story version.
        sch_dep -- list of dependency graphs for each sentence of
                    the sch version.
        sch_par -- list of constituency parses for each sentence of
                    the sch version.
        story_par -- list of constituency parses for each sentence of
                    the story version.
        sch --  the raw text for the sch version.
        text -- the raw text for the story version.
        sid --  the story id


    """
    return dependent(question, story)

   

#############################################################
###     Dont change the code in this section
#############################################################
class QAEngine(QABase):
    @staticmethod
    def answer_question(question, story):
        answer = get_answer(question, story)
        return str(answer)


def run_qa(evala=True):
    QA = QAEngine(evaluate=evala)
    QA.run()
    QA.save_answers()

#############################################################


def main():
    run_qa(evala=True)
    # You can uncomment this next line to evaluate your
    # answers, or you can run score_answers.py
    f = open("score.txt", "w")
    sys.stdout = f
    score_answers(get_the_q_count()) #FIXME Change before you turn in 
    sys.stdout = sys.__stdout__

if __name__ == "__main__":
    main()
