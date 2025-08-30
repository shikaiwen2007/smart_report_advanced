import os, fnmatch

folderpath = input("请输入要递归遍历文件夹的路径：")
if folderpath:
    folderpath = os.path.abspath(folderpath)
else:
    print("输入的文件夹路径无效，请重新输入")

skip_folder = '无问题'
problem_list = []
for path, dirs, files in os.walk(folderpath): # path：当前遍历到的目录路径 dirs：当前目录下的子目录列表 files：当前目录下的文件列表
    if skip_folder in dirs:
        dirs.remove(skip_folder)
    for filename in fnmatch.filter(files, "*.jpg"):
        problem_list.append(filename.split(".")[0])

print(problem_list)