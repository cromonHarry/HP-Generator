from prompt import *

hp_mt_0 = {}
hp_mt_1 = {}
hp_mt_2 = {}

# No.1-4, 4 user input
input1 = input("最近自分が別人と違う感じになった行動はありますか").strip()
input2 = input("それをじつげんするために、どんな製品やサービスを使っていますか").strip()
input3 = input("なぜそのような製品やサービスを使用するか").strip()
input4 = input("その行動を基づいて、どんな自分になりたいですか").strip()

hp_mt_1[HP_model[5]] = input1
hp_mt_1[HP_model[14]] = input2
hp_mt_1[HP_model[13]] = input3
hp_mt_1[HP_model[2]] = input4

# No.5, AI analyse
hp_mt_1[HP_model[9]] = tavily_generate_answer(generate_question_for_tavily(HP_model[2], hp_mt_1[HP_model[2]], HP_model[9], 1))
hp_mt_1[HP_model[11]] = tavily_generate_answer(generate_question_for_tavily(HP_model[2], hp_mt_1[HP_model[2]], HP_model[11], 1))
hp_mt_1[HP_model[3]] = tavily_generate_answer(generate_question_for_tavily(HP_model[2], hp_mt_1[HP_model[2]], HP_model[3], 1))
hp_mt_1[HP_model[8]] = tavily_generate_answer(generate_question_for_tavily(HP_model[3], hp_mt_1[HP_model[3]], HP_model[8], 1))
hp_mt_1[HP_model[1]] = tavily_generate_answer(generate_question_for_tavily(HP_model[8], hp_mt_1[HP_model[8]], HP_model[1], 1))
hp_mt_0[HP_model[16]] = tavily_generate_answer(generate_question_for_tavily(HP_model[1], hp_mt_1[HP_model[1]], HP_model[16], 0))
hp_mt_0[HP_model[4]] = tavily_generate_answer(generate_question_for_tavily(HP_model[16], hp_mt_0[HP_model[16]], HP_model[4], 0))
hp_mt_0[HP_model[18]] = tavily_generate_answer(generate_question_for_tavily(HP_model[1], hp_mt_1[HP_model[1]], HP_model[18], 0))
hp_mt_0[HP_model[5]] = tavily_generate_answer(generate_question_for_tavily(HP_model[18], hp_mt_0[HP_model[18]], HP_model[5], 0))
hp_mt_0[HP_model[6]] = tavily_generate_answer(generate_question_for_tavily(HP_model[3], hp_mt_1[HP_model[3]], HP_model[6], 0))
hp_mt_1[HP_model[4]] = tavily_generate_answer(generate_question_for_tavily(HP_model[14], hp_mt_1[HP_model[14]], HP_model[4], 1))
hp_mt_1[HP_model[17]] = tavily_generate_answer(generate_question_for_tavily(HP_model[5], hp_mt_1[HP_model[5]], HP_model[17], 1))
hp_mt_1[HP_model[15]] = tavily_generate_answer(generate_question_for_tavily(HP_model[2], hp_mt_1[HP_model[2]], HP_model[15], 1))
hp_mt_1[HP_model[6]] = tavily_generate_answer(generate_question_for_tavily(HP_model[17], hp_mt_1[HP_model[17]], HP_model[6], 1))
hp_mt_1[HP_model[6]] = tavily_generate_answer(generate_question_for_tavily(HP_model[15], hp_mt_1[HP_model[15]], HP_model[6], 1))
hp_mt_2[HP_model[10]] = single_gpt(HP_model[6], hp_mt_1[HP_model[6]], HP_model[10])
hp_mt_2[HP_model[4]] = single_gpt(HP_model[10], hp_mt_1[HP_model[10]], HP_model[4])
hp_mt_1[HP_model[18]] = tavily_generate_answer(generate_question_for_tavily(HP_model[5], hp_mt_1[HP_model[5]], HP_model[18], 1))
# 5个先导社会问题
hp_mt_2[HP_model[1]] = list_up_gpt(HP_model[5], hp_mt_1[HP_model[5]], HP_model[1])
hp_mt_2[HP_model[8]] = single_gpt(HP_model[1], hp_mt_2[HP_model[1]], HP_model[8])
# 5个社会问题
hp_mt_2[HP_model[3]] = list_up_gpt(HP_model[8], hp_mt_1[HP_model[8]], HP_model[3])
# 5个人的价值观
hp_mt_2[HP_model[2]] = list_up_gpt(HP_model[3], hp_mt_1[HP_model[3]], HP_model[2])
hp_mt_2[HP_model[9]] = single_gpt(HP_model[1], hp_mt_2[HP_model[1]], HP_model[9])
# 5个习惯化
hp_mt_2[HP_model[15]] = list_up_gpt(HP_model[2], hp_mt_1[HP_model[2]], HP_model[15])
# 5个UX空间
hp_mt_2[HP_model[5]] = list_up_gpt(HP_model[2], hp_mt_1[HP_model[2]], HP_model[5])
hp_mt_2[HP_model[14]] = single_gpt(HP_model[5], hp_mt_2[HP_model[5]], HP_model[14])
hp_mt_2[HP_model[4]] = single_gpt(HP_model[14], hp_mt_2[HP_model[14]], HP_model[4])