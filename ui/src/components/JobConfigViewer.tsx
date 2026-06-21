'use client';
import { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';

import { Job } from '@prisma/client';

interface Props {
  job: Job;
}

export default function JobConfigViewer({ job }: Props) {
  const [editorValue, setEditorValue] = useState<string>('');
  useEffect(() => {
    if (job?.job_config) {
      setEditorValue(job.job_config);
    }
  }, [job]);
  return (
    <>
      <Editor
        height="100%"
        width="100%"
        defaultLanguage="yaml"
        value={editorValue}
        theme="vs-dark"
        options={{
          minimap: { enabled: true },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          readOnly: true,
        }}
      />
    </>
  );
}
