import YAML from 'yaml';
import type { JobConfig } from '@/types';

export const yamlConfig: YAML.DocumentOptions &
  YAML.SchemaOptions &
  YAML.ParseOptions &
  YAML.CreateNodeOptions &
  YAML.ToStringOptions = {
  indent: 2,
  lineWidth: 999999999999,
  defaultStringType: 'QUOTE_DOUBLE',
  defaultKeyType: 'PLAIN',
  directives: true,
};

export const parseJobConfigText = (jobConfigText: string) => {
  return YAML.parse(jobConfigText) as JobConfig;
};

export const stringifyJobConfig = (jobConfig: JobConfig) => {
  return YAML.stringify(jobConfig, yamlConfig);
};
