import { pythonGenerator } from "blockly/python";

export const defineControlGenerators = () => {
    pythonGenerator.forBlock['control_wait'] = function (block) {
        const x = block.getFieldValue('x');
        return `CoronaEngine.wait(${x})\n`;
    };

    pythonGenerator.forBlock['control_for'] = function (block) {
        let branch = pythonGenerator.statementToCode(block, 'DO');
        if (pythonGenerator.STATEMENT_PREFIX) {
            branch = pythonGenerator.prefixLines(
                pythonGenerator.STATEMENT_PREFIX.replace(/%1/g, '\'' + block.id + '\''),
                pythonGenerator.INDENT) + branch;
        }
        // Use branch as-is (already indented by Blockly). If empty, insert a pass.
        if (!branch) branch = pythonGenerator.INDENT + 'pass\n';
        return `while True:\n` + branch;
    };

    // 定义重复执行 x 次积木块的 Python 代码生成器
    pythonGenerator.forBlock['control_forX'] = function (block) {
        const times = pythonGenerator.valueToCode(block, 'TIMES', pythonGenerator.ORDER_NONE) || block.getFieldValue('DEFAULT_TIMES');
        let branch = pythonGenerator.statementToCode(block, 'DO');
        if (!branch) branch = pythonGenerator.INDENT + 'pass\n';
        return `for _ in range(${times}):\n` + branch;
    };

    pythonGenerator.forBlock['control_if'] = function (block) {
        const condition = pythonGenerator.valueToCode(block, 'CONDITION', pythonGenerator.ORDER_NONE) || 'False';
        let branch = pythonGenerator.statementToCode(block, 'DO');
        if (!branch) branch = pythonGenerator.INDENT + 'pass\n';
        return `if ${condition}:\n` + branch;
    };

    // 定义如果那么否则积木块的 Python 代码生成器
    pythonGenerator.forBlock['control_else'] = function (block) {
        const condition = pythonGenerator.valueToCode(block, 'CONDITION', pythonGenerator.ORDER_NONE) || 'False';
        let branch = pythonGenerator.statementToCode(block, 'DO');
        let elseBranch = pythonGenerator.statementToCode(block, 'ELSE');
        if (!branch) branch = pythonGenerator.INDENT + 'pass\n';
        let code = `if ${condition}:\n` + branch;
        if (elseBranch !== null) {
            // If else exists but is empty, still output a pass.
            if (!elseBranch) elseBranch = pythonGenerator.INDENT + 'pass\n';
            code += `else:\n` + elseBranch;
        }
        return code;
    };

    // 定义等待直到条件满足积木块的 Python 代码生成器
    pythonGenerator.forBlock['control_wait2'] = function (block) {
        const condition = pythonGenerator.valueToCode(block, 'CONDITION', pythonGenerator.ORDER_NONE) || 'False';
        return `while not (${condition}):\n` + pythonGenerator.INDENT + 'pass\n';
    };

    // 定义重复执行直到积木块的 Python 代码生成器
    pythonGenerator.forBlock['control_until'] = function (block) {
        const condition = pythonGenerator.valueToCode(block, 'CONDITION', pythonGenerator.ORDER_NONE) || 'False';
        let branch = pythonGenerator.statementToCode(block, 'DO');
        if (!branch) branch = pythonGenerator.INDENT + 'pass\n';
        return `while not (${condition}):\n` + branch;
    };

    // 定义停止积木块的 Python 代码生成器
    pythonGenerator.forBlock['control_stop'] = function (block) {
        const stopOption = block.getFieldValue('STOP_OPTION');
        return `CoronaEngine.stop("${stopOption}")\n`;
    };

    pythonGenerator.forBlock['control_cloneStart'] = function () {
        return `CoronaEngine.cloneStart()\n`;
    };

    pythonGenerator.forBlock['control_clone'] = function (block) {
        const x = block.getFieldValue('x');
        return `CoronaEngine.clone(${x})\n`;
    };

    pythonGenerator.forBlock['control_cloneDEL'] = function () {
        return `CoronaEngine.deleteClone()\n`;
    };

    pythonGenerator.forBlock['control_senceSet'] = function (block) {
        const x = block.getFieldValue('x');
        return `CoronaEngine.setScene(${x})\n`;
    };

    pythonGenerator.forBlock['control_nextSence'] = function () {
        return `CoronaEngine.nextScene()\n`;
    };
}