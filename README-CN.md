# 自动跑命令的工具

该工具可以实现任何实验的自动测试和结果自动抽取、资源占用自动dump、输出log自动记录等功能。

## 功能介绍

工程用python2编写，最主要部分为`coordinator.py`文件。通过

```
python coordinator.py <exp_config> <result_file> <dump_file>
```

命令即可进行实验。

## 实验假设

在每一个实验设置文件中，均可以跑多个小实验，但是当前假设每一个小实验执行的命令都是一致的，如果需要有不同，通过环境变量来输入。
今后将（可能）会加入自定义每一个命令的args。

## 实验json结构

目前，在实验的设置文件为json格式。schema为如下

```
{
    "description": "experiment descrition here",
    "cmd": "cmd to run on each task, 例如 `./task`",
    "log_cmd": "得到result用的command, 例如 `tail -n 100 tmp.log | grep task` , 结果将在命令的输出中抽取",
    "monitor_cmds": [
        "adb shell dumpsys meminfo `adb shell ps | grep task | awk '{print $2}'` -d | grep -m 1 TOTAL | awk '{print $2}'",
        "adb shell top -m 15 -n 1 -s cpu | grep task | awk '{print $1, $3}'",
        "adb shell cpustats -m -n 1" // 用来dump系统信息的一系列指令，上面的例子为在android开发板dump task这个程序的内存占用、CPU使用率、各CPU分配情况的例子
    ],
    "result_per_exp": 1, // 默认为1，表示从log_cmd的返回中抽取结果的个数
    "env": {
        "X": 5,
        "DEBUG": "TRUE"
    }, // 这里设置的是全局的环境变量，即每个实验都会加入
    "exps": [
        {
            "name": "single_4", // 实验名称
            "env": {
                "DEBUG": "FALSE",
                "Y": 4
            } // 每个实验均可设置自己不同的环境变量，实验内比全局环境变量优先
        },
        {
            "name": "concurrent_6_2",
            "tasks": 6, // 同时运行的命令数，默认为1
            "result_per_exp": 6, // 默认为1，表示从log_cmd的返回中抽取结果的个数，实验设置覆盖全局设置
            "env": {
                "Y": 2
            }
        }
    ]
}
```

## 结果抽取规则

实验结果的抽取规则为:

在`log_cmd`得到的结果中，找到最后`result_per_exp`个符合正则表达式`'-->([^<>-]+)<--'`，即包含在`'-->'`和`'<--'`中的串，并输出到`<result_file>`中。

## 系统信息dump规则

系统信息dump时会将每一个`monitor_cmds`中的每一个命令的结果都记录在`<dump_file>`中
