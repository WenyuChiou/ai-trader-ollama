#!/bin/bash
# Linux/Mac 脚本 - 快速运行测试

echo "========================================"
echo "测试工具脚本"
echo "========================================"
echo ""
echo "请选择要运行的测试:"
echo "1. 测试所有工具"
echo "2. 测试基本面工具"
echo "3. 测试新闻工具"
echo "4. 测试技术分析工具"
echo "5. 测试市场工具"
echo "6. 测试情绪工具"
echo ""
read -p "请输入选项 (1-6): " choice

case $choice in
    1)
        python test/test_tools.py --category all
        ;;
    2)
        python test/test_tools.py --category fundamental
        ;;
    3)
        python test/test_tools.py --category news
        ;;
    4)
        python test/test_tools.py --category technical
        ;;
    5)
        python test/test_tools.py --category market
        ;;
    6)
        python test/test_tools.py --category sentiment
        ;;
    *)
        echo "无效选项"
        ;;
esac

