"use client";
import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion } from "framer-motion";

interface Message {
  id: number;
  role: "user" | "ai";
  content: string;
  timestamp: string;
}

export default function ChatbotUI() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [userIP, setUserIP] = useState<string>("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Fetch user's IP address on mount
  useEffect(() => {
    const fetchIP = async () => {
      try {
        const res = await fetch("https://api.ipify.org?format=json");
        const data = await res.json();
        setUserIP(data.ip);
      } catch (err) {
        console.error("Failed to fetch IP address:", err);
      }
    };
    fetchIP();
  }, []);

  const getCurrentTimestamp = () => {
    return new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const timestamp = getCurrentTimestamp();

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: input.trim(),
      timestamp,
    };

    // Add user's message to UI
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      // 🌟 Define the main instruction prompt
      const mainPrompt = `I need you to relate a message from me describing my problem, along with a Bhagavata Gita verse. you have to relate my problem with given verse, and describe the solution using the verse. Only once in your msg describe every problem's solution is in Bhagavat Gita, not in every msg only in the first msg and make it separate pargraph. Don't say **Connecting the Verse to Your Problem:** and enstead of  **Solution from the Verse:** say Solution: . Avoid greeding in the msg like "hello", "hii". In every msg instead of I use You.`;

      // 🌟 Build structured history including mainPrompt
      const conversationHistory = [
        { role: "user", content: mainPrompt },
        ...messages.map((msg) => ({
          role: msg.role === "ai" ? "model" : "user",
          content: msg.content,
        })),
      ];

      const response = await fetch("http://192.168.0.102:5000/user_msg_Api", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage.content,
          history: conversationHistory,
        }),
      });

      const data = await response.json();
      const aiResponse = data.gemini_response || "AI did not respond.";

      // Add AI response to UI
      const aiMessage: Message = {
        id: Date.now() + 1,
        role: "ai",
        content: aiResponse,
        timestamp: getCurrentTimestamp(),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error communicating with Flask API:", error);
      const errorMsg: Message = {
        id: Date.now() + 2,
        role: "ai",
        content: "There was an error contacting the Flask API.",
        timestamp: getCurrentTimestamp(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-800 dark:bg-gray-900">
      <div className="bg-blue-500 dark:bg-gray-800 rounded-md p-5 text-left mt-4">
        <h1 className="text-2xl font-semibold text-blue-100 dark:text-white">
          Smart ChatBot
        </h1>
        <p className="text-sm text-blue-200 mt-1">Your IP: {userIP}</p>
      </div>
      <Card className="flex-1 mt-2 bg-gray-100 overflow-hidden rounded-2xl shadow-md">
        <CardContent className="p-4 h-full flex flex-col">
          <ScrollArea className="flex-1 space-y-4 overflow-y-auto pr-2">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`w-full flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className={`p-3 rounded-xl max-w-xl w-fit relative ${
                    msg.role === "user"
                      ? "bg-blue-500 text-white"
                      : "bg-gray-200 dark:bg-gray-800 text-blue-700 dark:text-white"
                  }`}
                >
                  <pre className="whitespace-pre-wrap font-mono">
                    {msg.content}
                  </pre>
                  <div className="text-xs text-gray-300 dark:text-gray-500 mt-1 text-right">
                    {msg.timestamp}
                  </div>
                </motion.div>
              </div>
            ))}
            <div ref={bottomRef} />
          </ScrollArea>
          <div className="mt-4 flex gap-2">
            <Input
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 placeholder-red-300 bg-blue-400"
            />
            <Button onClick={handleSend}>Send</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
