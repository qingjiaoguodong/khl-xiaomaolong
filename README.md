# khl-xiaomaolong

*****

## Commit建议格式
```
[<type>](<scope>): <subject>  # This line is called as HEADER
# Blank line
<body>
# Blank line
<footer>
```
`<type>`:用于说明 commit 的类别，只允许使用下面8个标识。
> - `feat`: 新功能（feature）
> - `fix`: 修补bug
> - `docs`: 文档（documentation）
> - `style`: 格式（不影响代码运行的变动）
> - `refactor`: 重构（即不是新增功能，也不是修改bug的代码变动）
> - `test`: 增加测试
> - `chore`: 构建过程或辅助工具的变动
> - `revert`: 如果当前 commit 用于撤销以前的 commit，则必须以`revert:`开头，后面跟着被撤销 commit 的 `HEADER`。

`<scope>`(<u>optional</u>): `scope`用于说明 commit 影响的范围。

`<subject>`: `subject`是 commit 目的的简短描述。

`<body>`(<u>optional</u>): `body`部分是对本次 commit 的详细描述，可以分成多行。

`<footer>`(<u>optional</u>)

**If you can read this line, then use English to write your commit is strongly advised.**

参考资料: [git commit 规范指南](https://segmentfault.com/a/1190000009048911)
