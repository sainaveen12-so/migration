"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { aiApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ChatMessage {
  id: number;
  role: string;
  content: string;
  created_at: string;
}

interface AIChatProps {
  projectId: number;
  filePath?: string;
}

export function AIChat({ projectId, filePath }: AIChatProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: messages = [], isLoading } = useQuery({
    queryKey: ["chat", projectId],
    queryFn: async () => {
      const { data } = await aiApi.getChatHistory(projectId);
      return data as ChatMessage[];
    },
  });

  const sendMutation = useMutation({
    mutationFn: (content: string) => aiApi.chat(projectId, content, filePath),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat", projectId] });
      setInput("");
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || sendMutation.isPending) return;
    sendMutation.mutate(input);
  };

  const quickPrompts = [
    "Explain this project",
    "Where is authentication implemented?",
    "How is database connection created?",
    "Explain API flow",
    "Find bugs in this code",
    "Generate documentation",
  ];

  return (
    <div className="flex h-full flex-col rounded-lg border border-gray-200 dark:border-gray-800">
      <div className="border-b border-gray-200 p-3 dark:border-gray-800">
        <h3 className="font-medium">AI Assistant</h3>
        {filePath && <p className="text-xs text-gray-500">Context: {filePath}</p>}
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4" style={{ maxHeight: "400px" }}>
        {isLoading ? (
          <div className="flex justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : messages.length === 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-gray-500">Ask anything about your project:</p>
            <div className="flex flex-wrap gap-2">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => setInput(prompt)}
                  className="rounded-full border border-gray-200 px-3 py-1 text-xs hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`rounded-lg p-3 text-sm ${
                msg.role === "user"
                  ? "ml-8 bg-blue-50 dark:bg-blue-950"
                  : "mr-8 bg-gray-50 dark:bg-gray-900"
              }`}
            >
              <p className="mb-1 text-xs font-medium capitalize text-gray-500">{msg.role}</p>
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-2 border-t border-gray-200 p-3 dark:border-gray-800">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about your code..."
          disabled={sendMutation.isPending}
        />
        <Button onClick={handleSend} disabled={sendMutation.isPending || !input.trim()}>
          {sendMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
