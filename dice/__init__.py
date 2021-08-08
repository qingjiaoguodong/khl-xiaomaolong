'''
骰子/计算器工具
d100: 100面骰
2d100: 两个100面骰相加
2d100s: 两个100面骰里较小的那个
3d100s2: 三个100面骰里小的两个之和
3d100l2： 三个100面骰里大的两个之和
dp, db: CoC 7th惩罚骰、奖励骰
3dp: 等价于dp+dp+dp
9999999d9999999: 没事，骰子够多
d6*(d6+d6): 字面意思
d6!: d6的阶乘


可用运算符（含义同Python）：
+,-,*,/,%,//,**
可用函数：
exp,log,log10,sin,cos,abs,sqrt,ceil,floor,round,max,min
可用常量：
pi
'''

from .dice_roller import parse_and_eval_dice