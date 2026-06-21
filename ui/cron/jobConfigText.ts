import YAML from 'yaml';

export const parseJobConfigText = (jobConfigText: string) => {
  return YAML.parse(jobConfigText);
};

export const stringifyJobConfig = (jobConfig: unknown) => {
  return YAML.stringify(jobConfig, {
    indent: 2,
    lineWidth: 999999999999,
    defaultStringType: 'QUOTE_DOUBLE',
    defaultKeyType: 'PLAIN',
    directives: true,
  });
};
