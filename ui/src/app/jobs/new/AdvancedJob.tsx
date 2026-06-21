'use client';
import { useEffect, useState, useRef } from 'react';
import { JobConfig } from '@/types';
import YAML from 'yaml';
import Editor, { OnMount } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import { Settings } from '@/hooks/useSettings';
import { migrateJobConfig } from './jobConfig';
import { stringifyJobConfig } from '@/utils/jobConfigText';

type Props = {
  jobConfig: JobConfig;
  setJobConfig: (value: any, key?: string) => void;
  status: 'idle' | 'saving' | 'success' | 'error';
  handleSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  runId: string | null;
  gpuIDs: string | null;
  setGpuIDs: (value: string | null) => void;
  gpuList: any;
  datasetOptions: any;
  settings: Settings;
  yamlConfigText: string | null;
  onYamlChange: (value: string, isValid: boolean) => void;
};

const isDev = process.env.NODE_ENV === 'development';

export default function AdvancedJob({ jobConfig, setJobConfig, settings, yamlConfigText, onYamlChange }: Props) {
  const [editorValue, setEditorValue] = useState<string>('');
  const [parseError, setParseError] = useState<string | null>(null);
  const lastRenderedJobConfigStringRef = useRef('');
  const lastParsedJobConfigStringRef = useRef('');
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const isApplyingEditorValueRef = useRef(false);
  const programmaticEditorValueRef = useRef<string | null>(null);
  const hasUserEditedRef = useRef(false);

  // Track if the editor has been mounted
  const isEditorMounted = useRef(false);

  const getYamlFromJobConfig = (config: JobConfig) => stringifyJobConfig(config);

  const getErrorMessage = (error: unknown) => {
    if (error instanceof Error) return error.message;
    return `${error}`;
  };

  const applyRequiredConfigDefaults = (config: any) => {
    try {
      // config.config.process[0].type = 'ui_trainer';
      config.config.process[0].sqlite_db_path = './aitk_db.db';
      config.config.process[0].training_folder = settings.TRAINING_FOLDER;
      config.config.process[0].device = 'cuda';
      config.config.process[0].performance_log_every = 10;
    } catch (e) {
      if (isDev) console.warn(e);
    }

    return migrateJobConfig(config);
  };

  const parseYamlJobConfig = (value: string) => {
    const document = YAML.parseDocument(value, { prettyErrors: true });
    if (document.errors.length > 0) {
      throw document.errors[0];
    }

    const parsed = document.toJS();
    if (parsed === null || typeof parsed !== 'object') {
      throw new Error('YAML must contain a job config object.');
    }

    return applyRequiredConfigDefaults(parsed);
  };

  const applyEditorValue = (value: string) => {
    isApplyingEditorValueRef.current = true;
    programmaticEditorValueRef.current = value;
    setEditorValue(value);

    const editor = editorRef.current;
    if (editor && editor.getValue() !== value) {
      editor.getModel()?.setValue(value);
    }

    queueMicrotask(() => {
      isApplyingEditorValueRef.current = false;
    });
  };

  // Handler for editor mounting
  const handleEditorDidMount: OnMount = editor => {
    editorRef.current = editor;
    isEditorMounted.current = true;

    // Initial content setup
    try {
      const yamlContent = yamlConfigText ?? getYamlFromJobConfig(jobConfig);
      const jobConfigString = JSON.stringify(jobConfig);
      applyEditorValue(yamlContent);
      onYamlChange(yamlContent, true);
      lastRenderedJobConfigStringRef.current = jobConfigString;
      lastParsedJobConfigStringRef.current = jobConfigString;
    } catch (e) {
      if (isDev) console.warn(e);
    }
  };

  useEffect(() => {
    const currentUpdate = JSON.stringify(jobConfig);

    // This update came from a valid YAML edit. Keep the user's raw YAML exactly
    // as typed so comments and block scalar formatting survive the round trip.
    if (lastParsedJobConfigStringRef.current === currentUpdate) {
      lastRenderedJobConfigStringRef.current = currentUpdate;
      return;
    }

    // Skip if no changes or editor not yet mounted
    if (lastRenderedJobConfigStringRef.current === currentUpdate || !isEditorMounted.current) {
      return;
    }

    if (hasUserEditedRef.current) {
      return;
    }

    try {
      // Preserve cursor position and selection
      const editor = editorRef.current;
      if (editor) {
        // Save current editor state
        const position = editor.getPosition();
        const selection = editor.getSelection();
        const scrollTop = editor.getScrollTop();

        // Update content
        const yamlContent = getYamlFromJobConfig(jobConfig);

        // Only update if the content is actually different
        if (yamlContent !== editor.getValue()) {
          // Set value directly on the editor model instead of using React state
          hasUserEditedRef.current = false;
          applyEditorValue(yamlContent);

          // Restore cursor position and selection
          if (position) editor.setPosition(position);
          if (selection) editor.setSelection(selection);
          editor.setScrollTop(scrollTop);
        }

        lastRenderedJobConfigStringRef.current = currentUpdate;
        lastParsedJobConfigStringRef.current = currentUpdate;
      }
    } catch (e) {
      if (isDev) console.warn(e);
    }
  }, [jobConfig]);

  const handleChange = (value: string | undefined) => {
    if (value === undefined) return;
    setEditorValue(value);

    if (isApplyingEditorValueRef.current) {
      return;
    }
    if (programmaticEditorValueRef.current !== null) {
      if (programmaticEditorValueRef.current === value) {
        programmaticEditorValueRef.current = null;
        return;
      }
      programmaticEditorValueRef.current = null;
    }
    hasUserEditedRef.current = true;

    try {
      const parsed = parseYamlJobConfig(value);
      const parsedString = JSON.stringify(parsed);

      setParseError(null);
      onYamlChange(value, true);
      if (parsedString !== lastParsedJobConfigStringRef.current) {
        lastParsedJobConfigStringRef.current = parsedString;
        setJobConfig(parsed);
      }
    } catch (e) {
      // Don't update on parsing errors
      setParseError(getErrorMessage(e));
      onYamlChange(value, false);
      if (isDev) console.warn(e);
    }
  };

  return (
    <div className="relative h-full w-full">
      <Editor
        height="100%"
        width="100%"
        defaultLanguage="yaml"
        value={editorValue}
        theme="vs-dark"
        onChange={handleChange}
        onMount={handleEditorDidMount}
        options={{
          minimap: { enabled: true },
          scrollBeyondLastLine: false,
          automaticLayout: true,
        }}
      />
      {parseError && (
        <div className="absolute bottom-3 left-3 right-3 rounded-md border border-red-500/40 bg-red-950/95 px-3 py-2 text-sm text-red-100 shadow-lg">
          {parseError}
        </div>
      )}
    </div>
  );
}
