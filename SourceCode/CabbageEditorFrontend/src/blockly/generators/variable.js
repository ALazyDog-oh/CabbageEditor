import { pythonGenerator } from "blockly/python";

export const defineVariableGenerators = () => {
pythonGenerator.forBlock['variable_add'] = function(block) {
  const v = block.getFieldValue('v');
  const x = parseFloat(block.getFieldValue('x') || '0.0').toFixed(1);
  return `CabbageEngine.add(${v},${x})\n`;
};

pythonGenerator.forBlock['variable_set'] = function(block) {
  const v = block.getFieldValue('v');
  const x = parseFloat(block.getFieldValue('x') || '0.0').toFixed(1);
  return `CabbageEngine.set(${v},${x})\n`;
};

pythonGenerator.forBlock['variable_show'] = function(block) {
  const v = block.getFieldValue('v');
  return `CabbageEngine.show(${v})\n`;
};

pythonGenerator.forBlock['variable_hide'] = function(block) {
  const v = block.getFieldValue('v');
  return `CabbageEngine.hide(${v})\n`;
};
}