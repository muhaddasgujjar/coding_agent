import React, { useState, useEffect } from 'react';
import Editor from "@monaco-editor/react";
import { Folder, FileCode, Send, Loader2, FolderOpen, Code2 } from "lucide-react";

export default function App() {
  const [hasWorkspace, setHasWorkspace] = useState(false);
  const [workspacePath, setWorkspacePath] = useState("");
  
  const [files, setFiles] = useState([]);
  const [currentFile, setCurrentFile] = useState(null);
  const [editorContent, setEditorContent] = useState("# Select a file on the left to view code, or ask the agent to build something on the right.");
  const [chatHistory, setChatHistory] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [isThinking, setIsThinking] = useState(false);

  // Choose Workspace Native Prompt
  const handleChooseWorkspace = async () => {
    try {
      const res = await fetch('/api/choose-workspace');
      const data = await res.json();
      if(data.success && data.path) {
          setWorkspacePath(data.path);
          setHasWorkspace(true);
          
          setChatHistory([
            { sender: "System", text: `Active Workspace loaded:\n${data.path}\n\nWhat can I build for you?`, type: "agent" }
          ]);
          
          fetchFiles();
      }
    } catch(err) {
      console.error(err);
    }
  };

  // Fetch Files
  const fetchFiles = async () => {
    try {
      const res = await fetch('/api/files');
      const data = await res.json();
      if(data.files) setFiles(data.files);
    } catch(err) {
      console.error(err);
    }
  };

  const loadFile = async (filename) => {
    try {
      setCurrentFile(filename);
      setEditorContent("Loading...");
      const res = await fetch(`/api/file?name=${encodeURIComponent(filename)}`);
      const data = await res.json();
      setEditorContent(data.content || "");
    } catch(err) {
      console.error(err);
      setEditorContent("Error loading file.");
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if(!prompt.trim() || isThinking) return;

    const userPrompt = prompt.trim();
    setPrompt("");
    setChatHistory(prev => [...prev, { sender: "You", text: userPrompt, type: "user" }]);
    setIsThinking(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userPrompt, code: editorContent })
      });
      const data = await res.json();
      
      if(data.plan) setChatHistory(prev => [...prev, { sender: "Agent Plan", text: data.plan, type: "agent" }]);
      if(data.code) {
         setEditorContent(data.code);
         fetchFiles(); // update file list magically
      }
      if(data.error) setChatHistory(prev => [...prev, { sender: "Execution Failed", text: `${data.error}\n\n${data.output}`, type: "error" }]);
      else if(data.output) setChatHistory(prev => [...prev, { sender: "Execution Output", text: data.output, type: "agent" }]);
      else setChatHistory(prev => [...prev, { sender: "System", text: "Finished successfully.", type: "agent" }]);

    } catch(err) {
      setChatHistory(prev => [...prev, { sender: "System Error", text: err.message, type: "error" }]);
    } finally {
      setIsThinking(false);
    }
  };

  // --- WELCOME SCREEN VIEW ---
  if (!hasWorkspace) {
      return (
          <div className="flex flex-col items-center justify-center h-screen w-screen bg-darkBg text-gray-200 font-sans">
              <div className="max-w-md w-full bg-panelBg p-8 rounded-2xl shadow-2xl border border-gray-800 text-center space-y-6">
                  
                  <div className="flex justify-center mb-6">
                      <div className="p-4 bg-gray-900 rounded-full shadow-inner border border-gray-800/50">
                          <Code2 size={48} className="text-brandAccent" />
                      </div>
                  </div>

                  <div>
                      <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent mb-2">
                          Coding Agent IDE
                      </h1>
                      <p className="text-gray-400 text-sm">
                          To securely begin, select a local folder to open as your active workspace.
                      </p>
                  </div>
                  
                  <button onClick={handleChooseWorkspace} className="w-full bg-brandAccent hover:bg-[#20944e] transition text-white font-medium text-lg px-6 py-4 rounded-xl shadow-lg border border-green-600/50 flex flex-col items-center justify-center gap-2 group">
                      <FolderOpen size={24} className="group-hover:scale-110 transition-transform" />
                      Open Workspace Folder
                  </button>

                  <div className="text-xs text-gray-600 pt-4 border-t border-gray-800">
                      The Agent will only be able to interact with and edit code files implicitly inside the selected directory tree.
                  </div>

              </div>
          </div>
      );
  }

  // --- MAIN IDE VIEW ---
  return (
    <div className="flex h-screen w-screen bg-darkBg text-gray-300 font-sans overflow-hidden">
      
      {/* LEFT PANE: File Explorer */}
      <div className="w-1/6 flex flex-col bg-panelBg border-r border-gray-800 shadow-xl z-20">
         <div className="p-4 border-b border-gray-800 flex flex-col justify-center">
           <span className="flex items-center gap-2 font-bold text-gray-200">
               <Folder size={18} className="text-brandAccent" /> Workspace
           </span>
         </div>
         <div className="flex-grow overflow-auto p-2">
           {files.map(f => (
             <button key={f} onClick={() => loadFile(f)} className={`w-full text-left px-3 py-2 text-sm rounded flex items-center gap-2 mb-1 transition ${currentFile === f ? 'bg-gray-800 text-brandAccent font-medium' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'}`}>
               <FileCode size={16} className={currentFile === f ? 'text-brandAccent' : 'text-gray-500'} /> 
               {f}
             </button>
           ))}
         </div>
      </div>

      {/* MIDDLE PANE: Monaco Editor (IDE) */}
      <div className="w-3/6 flex flex-col bg-[#1e1e1e] border-r border-gray-800 relative shadow-2xl z-10">
         <div className="px-4 py-3 text-sm text-gray-400 font-mono border-b border-gray-800 bg-[#15171c] flex justify-between items-center shadow-sm">
             <div className="flex items-center gap-2"><FileCode size={16} /> {currentFile || "scratchpad.py"}</div>
         </div>
         <div className="flex-grow">
            <Editor
              height="100%"
              theme="vs-dark"
              language="python"
              value={editorContent}
              onChange={(value) => setEditorContent(value)}
              options={{ minimap: { enabled: false }, fontSize: 13, wordWrap: 'on' }}
            />
         </div>
      </div>

      {/* RIGHT PANE: Chat Interface */}
      <div className="w-2/6 flex flex-col bg-[#1a1d24] relative z-20 shadow-2xl">
        <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-[#15171c]">
            <span className="font-semibold text-gray-200">AI Assistant</span>
            {isThinking ? (
                <span className="flex items-center gap-2 text-yellow-500 text-xs px-2 py-1 bg-yellow-900/30 rounded-full animate-pulse border border-yellow-700/50">
                    <Loader2 size={12} className="animate-spin"/> Thinking
                </span>
            ) : (
                <span className="text-brandAccent text-xs px-2 py-1 bg-[#23a559]/20 rounded-full border border-[#23a559]/30">Ready</span>
            )}
        </div>
        
        <div className="flex-grow overflow-y-auto p-4 flex flex-col gap-3">
          {chatHistory.map((m, i) => (
             <div key={i} className={`p-3 rounded text-sm whitespace-pre-wrap break-words shadow-md border-l-4 ${m.type === 'user' ? 'bg-[#2b2d31] border-blue-500' : m.type === 'error' ? 'bg-[#3f1c1c] border-red-500' : 'bg-[#1e1f22] border-brandAccent text-gray-200'}`}>
               <span className="font-bold text-gray-400 block mb-1 text-xs uppercase tracking-wider">{m.sender}</span>
               {m.text}
             </div>
          ))}
        </div>

        <div className="p-4 bg-[#15171c] border-t border-gray-800">
           <form onSubmit={handleChat} className="flex flex-col gap-2 relative">
             <textarea 
               rows="3" 
               className="w-full bg-[#0f1115] text-gray-200 border border-gray-800 rounded p-3 text-sm focus:outline-none focus:border-brandAccent resize-none transition shadow-inner"
               placeholder="Instruct the agent..."
               value={prompt}
               onChange={e => setPrompt(e.target.value)}
               onKeyDown={e => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleChat(e); } }}
             />
             <div className="flex justify-end pt-1">
                <button type="submit" disabled={isThinking} className="bg-brandAccent/90 hover:bg-brandAccent disabled:opacity-50 text-white px-4 py-1.5 rounded flex items-center gap-2 text-sm font-medium transition shadow-lg">
                   <Send size={16}/> Submit
                </button>
             </div>
           </form>
        </div>
      </div>

    </div>
  );
}
