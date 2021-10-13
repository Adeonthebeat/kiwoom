codeList = ["000020", "000040", "000050", "000060"]
f = open("buy_list.txt", 'wt')
for code in codeList:
    # print(code)
    # f.write("매수;")
    # f.write(str(code))
    # f.write(";시장가;")
    # f.write("10;0;")
    # f.write("매수전\n")
    f.writelines("매수;" + code + ";시장가;10;0;매수전\n")
f.close()