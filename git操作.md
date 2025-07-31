# 1. 备份当前代码（不包括.git）
cp -r . ../OCR_api_test_backup
rm -rf ../OCR_api_test_backup/.git

# 2. 删除当前Git仓库
rm -rf .git

# 3. 重新初始化Git
git init

# 4. 确保.gitignore正确（您已经配置好了）

# 5. 添加文件（这次会自动排除大文件）
git add .

# 6. 检查要提交的文件大小
git ls-files | xargs ls -la | awk '{sum += $5} END {print "Total size: " sum/1024/1024 " MB"}'

# 7. 提交
git commit -m "Initial commit: 智能学术论文处理系统（已排除大文件）"

# 8. 添加远程仓库
git remote add origin https://github.com/Rostopher/llm_read_paper.git

# 9. 推送
git push -u origin main --force