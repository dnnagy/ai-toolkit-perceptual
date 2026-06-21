import { defaultDatasetsFolder, defaultDataRoot, defaultModelsFolder, defaultTimestepCurvesFolder, defaultTimestepDistributionsFolder } from '@/paths';
import { defaultTrainFolder } from '@/paths';
import NodeCache from 'node-cache';
import prisma from '@/server/prisma';

const myCache = new NodeCache();

export const flushCache = () => {
  myCache.flushAll();
};

const getSettingValue = async (key: string, fallback: string) => {
  let value = myCache.get(key) as string;
  if (value) {
    return value;
  }

  try {
    const row = await prisma.settings.findFirst({
      where: { key },
    });
    value = row?.value && row.value !== '' ? row.value : fallback;
  } catch (error) {
    console.error(`Failed to load setting ${key}, using default:`, error);
    value = fallback;
  }

  myCache.set(key, value);
  return value;
};

export const getDatasetsRoot = async () => {
  return getSettingValue('DATASETS_FOLDER', defaultDatasetsFolder);
};

export const getTrainingFolder = async () => {
  return getSettingValue('TRAINING_FOLDER', defaultTrainFolder);
};

export const getHFToken = async () => {
  return getSettingValue('HF_TOKEN', '');
};

export const getModelsRoot = async () => {
  return getSettingValue('MODELS_FOLDER', defaultModelsFolder);
};

export const getTimestepCurvesRoot = async () => {
  return getSettingValue('TIMESTEP_CURVES_FOLDER', defaultTimestepCurvesFolder);
};

export const getTimestepDistributionsRoot = async () => {
  return getSettingValue('TIMESTEP_DISTRIBUTIONS_FOLDER', defaultTimestepDistributionsFolder);
};

export const getDataRoot = async () => {
  return getSettingValue('DATA_ROOT', defaultDataRoot);
};
