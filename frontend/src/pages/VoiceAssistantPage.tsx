import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useCivicScore } from '../context/CivicScoreContext';
import {
  Mic, Square, Send, Bot, User, Volume2, VolumeX,
  RotateCcw, Sparkles, MapPin, TrendingUp, AlertCircle,
  ChevronRight, Zap, Clock, Star, MessageSquare, Activity
} from 'lucide-react';
import { cn } from '../lib/utils';
import {
  fetchMultiScaleAnalytics,
  fetchUnderservedRankings,
  fetchDashboardRecommendations,
} from '../services/dashboardService';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  isTyping?: boolean;
  cards?: QuickCard[];
}

interface QuickCard {
  label: string;
  value: string;
  color: string;
  icon: string;
}

// ─── Knowledge base built from live + demo data ───────────────────────────────

const CIVIC_KB = {
  areas: ['Rajwada', 'Sarafa', 'Old Palasia', 'Vijay Nagar', 'Bhanwarkuan'],
  zones: ['Zone 1 - Rajwada Central', 'Zone 2 - Palasia East', 'Zone 3 - Vijay Nagar North', 'Zone 4 - Bhanwarkuan South'],
  categories: ['healthcare', 'education', 'transport', 'water', 'market'],
  criticalIssues: [
    'Vijay Nagar has no local hospital — 22,000 residents must travel 25+ minutes to MY Hospital.',
    'Bhanwarkuan BRTS Bus Hub is temporarily closed for corridor repairs.',
    'Palasia Health Center is critically overloaded with over 50 patients waiting.',
    'Bhanwarkuan Sector 4 Community Well has low water pressure and contamination risk.',
  ],
  tips: [
    'Submit a report with a photo to earn +15 Civic Points.',
    'Verified reports earn up to +10 bonus points from authorities.',
    'You can simulate new facility placement in the Scenario Lab.',
    'Use the Civic Map to explore real-time accessibility scores.',
    'Switch to City scale on the Dashboard for a full Indore overview.',
  ],
};

const SUGGESTED_QUESTIONS = [
  'Which area has the worst healthcare access?',
  'What are the top civic issues right now?',
  'How do I earn more civic points?',
  'What is the accessibility score for Vijay Nagar?',
  'Which service category needs most investment?',
  'How does the scoring system work?',
  'Show me underserved areas in Indore',
  'What is a civic desert?',
];

// ─── Local AI Engine (no external API needed) ─────────────────────────────────

function generateResponse(input: string, contextData: any, user: any): { text: string; cards?: QuickCard[] } {
  const q = input.toLowerCase().trim();
  
  // Greetings
  if (/^(hi|hello|hey|namaste|helo)/.test(q)) {
    return {
      text: `Hello ${user?.name?.split(' ')[0] || 'there'}! 👋 I'm **CivicBot**, your AI assistant for CivicPulse Indore. I can help you with:\n\n• **Civic issues** — what problems exist in which areas\n• **Your score** — how to earn more Civic Points\n• **Data insights** — accessibility scores, rankings, trends\n• **Navigation** — finding features in the app\n\nWhat would you like to know?`,
    };
  }

  // Worst healthcare / critical health
  if (/healthcare|hospital|clinic|health|medical/.test(q) && /worst|bad|critical|no|need|lack/.test(q)) {
    return {
      text: `🏥 **Healthcare Access Crisis in Indore:**\n\n**Vijay Nagar** is the most critical healthcare desert in our dataset:\n• **22,000+ residents** have zero local healthcare facility\n• The nearest government hospital (MY Hospital) is **25+ minutes away in traffic**\n• Accessibility score: critically low\n\n**Palasia Health Center** is also severely overloaded — patients wait over 1 hour for basic triage.\n\n**Recommended action:** The Scenario Lab can simulate placing a new clinic in Vijay Nagar to estimate the impact.`,
      cards: [
        { label: 'Vijay Nagar', value: 'No hospital', color: 'bg-red-50 border-red-200 text-red-700', icon: '🚨' },
        { label: 'Palasia Center', value: 'Overloaded', color: 'bg-orange-50 border-orange-200 text-orange-700', icon: '⚠️' },
        { label: 'MY Hospital', value: '25 min away', color: 'bg-amber-50 border-amber-200 text-amber-700', icon: '🏥' },
      ],
    };
  }

  // Top issues / current problems
  if (/top|current|main|biggest|critical|issues|problems|alerts/.test(q)) {
    return {
      text: `🚨 **Top 4 Active Civic Issues in Indore:**\n\n1. 🏥 **Vijay Nagar** — No healthcare facility for 22,000 residents *(Critical)*\n2. 🚌 **Bhanwarkuan BRTS** — Bus hub closed for corridor repairs *(High)*\n3. 💧 **Bhanwarkuan Well** — Water contamination and pressure issues *(High)*\n4. 🏥 **Palasia Health Center** — Severe overcrowding and triage delays *(Medium)*\n\nAll these reports are community-verified. You can explore them on the **Civic Map** or submit a related field report to earn Civic Points.`,
      cards: [
        { label: 'Healthcare', value: '2 issues', color: 'bg-red-50 border-red-200 text-red-700', icon: '🏥' },
        { label: 'Transport', value: '1 issue', color: 'bg-orange-50 border-orange-200 text-orange-700', icon: '🚌' },
        { label: 'Water', value: '1 issue', color: 'bg-blue-50 border-blue-200 text-blue-700', icon: '💧' },
      ],
    };
  }

  // Civic points / score
  if (/point|score|civic|earn|badge|level|rank/.test(q)) {
    return {
      text: `⭐ **How the Civic Score System Works:**\n\n**Earning Points:**\n• **+10** — Submit a complete report\n• **+5** — Attach a photo\n• **+2** — Write a detailed description (100+ chars)\n• **+3** — Report a high/critical severity issue\n• **+up to 10** — Community/authority verification bonus\n\n**Levels:**\n👁️ Observer (0) → 📝 Reporter (50) → 📣 Advocate (150) → 🛡️ Guardian (300) → 🏆 Champion (500) → ⭐ Legend (1000)\n\n**Tips to rank up fast:**\n• Always add a photo to your reports\n• Focus on high-severity issues\n• Report regularly — 5 reports earns the "Civic Voice" 📢 badge`,
    };
  }

  // Vijay Nagar specific
  if (/vijay.?nagar/.test(q)) {
    return {
      text: `📍 **Vijay Nagar — Zone 3 North, Indore**\n\n**Population:** 22,000 residents\n**Classification:** Civic Desert (Healthcare)\n\n**Key Issues:**\n• ❌ Zero healthcare facilities in the entire neighbourhood\n• 🚌 Transport connectivity is limited to main arteries\n• 🏫 Education access is relatively better\n\n**Data insights:**\n• Accessibility Score: Very Low\n• Gap Score: Critical\n• Most underserved: Healthcare category\n\n**What you can do:**\n1. Submit a report about specific local issues\n2. Use Scenario Lab to simulate a new clinic placement\n3. Explore the Civic Map and filter by Healthcare`,
      cards: [
        { label: 'Population', value: '22,000', color: 'bg-slate-50 border-slate-200 text-slate-700', icon: '👥' },
        { label: 'Healthcare', value: 'Desert', color: 'bg-red-50 border-red-200 text-red-700', icon: '🏥' },
        { label: 'Gap Score', value: 'Critical', color: 'bg-red-50 border-red-200 text-red-700', icon: '📊' },
      ],
    };
  }

  // Bhanwarkuan specific
  if (/bhanwarkuan|bhanwar/.test(q)) {
    return {
      text: `📍 **Bhanwarkuan — Zone 4 South, Indore**\n\n**Population:** 15,000 residents\n**Vulnerability Index:** 0.74 (Very High)\n\n**Active Issues:**\n• 🚌 BRTS Bus Hub closed — buses diverted to ring road\n• 💧 Sector 4 Well: contamination + low pressure (field-confirmed)\n\n**Key Stats:**\n• Child dependency ratio: 38%\n• Elderly population: 21%\n• Both metrics flag this as a **high-vulnerability zone**\n\nField technicians have been dispatched for the water issue. Monitor updates on the Civic Map.`,
      cards: [
        { label: 'BRTS Hub', value: 'Closed', color: 'bg-orange-50 border-orange-200 text-orange-700', icon: '🚌' },
        { label: 'Water Well', value: 'Alert', color: 'bg-blue-50 border-blue-200 text-blue-700', icon: '💧' },
        { label: 'Vulnerability', value: '0.74 / High', color: 'bg-red-50 border-red-200 text-red-700', icon: '⚠️' },
      ],
    };
  }

  // Underserved / worst areas
  if (/underserved|worst|rank|bottom|desert|poor/.test(q)) {
    const areas = contextData?.rankings?.slice(0, 3);
    if (areas?.length) {
      const list = areas.map((a: any, i: number) =>
        `${i + 1}. **${a.area_name}** — Gap Score: ${a.gap_score?.toFixed(2) || 'N/A'} | ${a.desert_classification}`
      ).join('\n');
      return {
        text: `📊 **Top Underserved Areas (Live Data):**\n\n${list}\n\nThese rankings are generated by our deterministic accessibility engine using population, service distance, and capacity data from OpenStreetMap and government records.`,
      };
    }
    return {
      text: `📊 **Most Underserved Areas in Indore:**\n\n1. **Vijay Nagar** — Healthcare Desert, 22k population impacted\n2. **Bhanwarkuan** — Transport + Water issues, high vulnerability\n3. **Old Palasia** — Overloaded health center\n\nVisit the **Dashboard** for live underserved rankings and switch to Neighbourhood scale for detailed scores.`,
    };
  }

  // Scenario lab / simulation
  if (/scenario|simulation|simulate|what.?if|lab|new.*(hospital|clinic|school|bus|market)/.test(q)) {
    return {
      text: `🔬 **Scenario Lab — What-If Simulation**\n\nThe Scenario Lab lets you simulate adding new civic infrastructure and instantly see the estimated impact:\n\n**Facility types you can simulate:**\n🏥 Hospital / Clinic · 🏫 School · 🚌 Bus Stop · 💧 Water Point · 🛒 Market\n\n**What it shows:**\n• Before vs After accessibility score\n• Population coverage improvement\n• Nearest-service distance reduction\n• Travel time savings\n• Underserved area ranking change\n\n**How to use:**\n1. Go to **Scenario Lab** in the top navigation\n2. Click anywhere on the map to drop a simulation pin\n3. Select the facility type\n4. See the impact analysis instantly\n\n*All projections are estimates based on our spatial model.*`,
    };
  }

  // How scoring / methodology works
  if (/methodology|how.*work|algorithm|scoring|calcul|engine/.test(q)) {
    return {
      text: `⚙️ **CivicPulse Analytics Engine:**\n\nOur deterministic scoring model uses:\n\n**Accessibility Score (0–100)**\n• Distance to nearest service facility\n• Population density weighting\n• Service capacity vs current load\n\n**Gap Score**\n• Difference between expected and actual service coverage\n• Higher = worse underservice\n\n**Desert Classification**\n• *Critical Desert* → Score < 20\n• *Moderate Desert* → Score 20–45\n• *Acceptable* → Score 45–70\n• *Well-Served* → Score > 70\n\n**Data Sources:** OpenStreetMap (trust 0.85), Government Records (trust 0.95), Community Reports (trust 0.75)\n\nView the full methodology in the **Methodology** page.`,
    };
  }

  // What is civic desert
  if (/civic.?desert|desert|what is/.test(q)) {
    return {
      text: `🏜️ **What is a Civic Desert?**\n\nA **Civic Desert** is an area where residents have significantly below-average access to essential public services like healthcare, education, transport, water, or markets.\n\n**Classification thresholds:**\n• 🔴 **Critical Desert** — Accessibility Score < 20 (severe neglect)\n• 🟠 **Moderate Desert** — Score 20–45 (significant gaps)\n• 🟡 **Service Gap** — Score 45–70 (needs improvement)\n• 🟢 **Well Served** — Score > 70 (adequate coverage)\n\n**In Indore currently:**\nVijay Nagar is classified as a **Critical Healthcare Desert** — the most severe classification. This means residents there face a genuine public health risk from lack of access.\n\nCivicPulse uses this classification to prioritize investment recommendations.`,
    };
  }

  // How to report / submit
  if (/report|submit|how.*(report|submit)|issue.*report/.test(q)) {
    return {
      text: `📝 **How to Submit a Civic Report:**\n\n**Step 1: Describe the issue**\nUse the 🎤 Voice button to speak your description, or type it manually. The AI auto-detects the category from your words!\n\n**Step 2: Fill the details**\n• Issue Category (auto-suggested from voice)\n• Location / Area name\n• Severity level\n• Detailed description\n\n**Step 3: Add photo evidence (+5 pts)**\nAttach a photo to earn extra Civic Points and increase report credibility.\n\n**Rules:**\n• Minimum 20-character description required\n• Duplicate reports (same category + location in 30 min) are blocked\n• Points awarded only after successful submission\n\nGo to **Report Reality** in the navigation to submit now!`,
    };
  }

  // Navigate app
  if (/navigate|go to|open|show|take me|where is/.test(q)) {
    return {
      text: `🧭 **CivicPulse Navigation Guide:**\n\n• 📊 **Dashboard** — Overview metrics, rankings, charts for Indore\n• 🗺️ **Civic Map** — Interactive OpenStreetMap with facility layers\n• 🔬 **Scenario Lab** — Simulate new infrastructure placement\n• 📖 **Methodology** — How our scoring engine works\n• 🎙️ **Voice Assistant** — That's me! Ask anything civic\n• 📝 **Report Reality** — Submit community civic reports (Citizens only)\n\nJust click the link in the top navigation bar to go to any page.`,
    };
  }

  // Investment / recommendation
  if (/invest|recommend|priority|budget|where.*build|best.*place/.test(q)) {
    return {
      text: `💡 **Investment Recommendations for Indore:**\n\nBased on our accessibility engine and gap scores:\n\n**Priority 1 — Healthcare, Vijay Nagar**\nBuild a Primary Health Centre. Impact: 22,000 residents, eliminates a Critical Desert.\n\n**Priority 2 — Transport, Bhanwarkuan**\nRestore BRTS connectivity. Impact: 15,000 residents + high-vulnerability demographics.\n\n**Priority 3 — Water, Bhanwarkuan**\nRepair Sector 4 well infrastructure. Impact: Eliminates contamination risk.\n\n**Priority 4 — Healthcare Capacity, Palasia**\nExpand Palasia Health Center or add a satellite clinic to reduce load.\n\nUse the **Scenario Lab** to model the exact ROI of any of these interventions.`,
      cards: [
        { label: 'Healthcare', value: 'Vijay Nagar', color: 'bg-red-50 border-red-200 text-red-700', icon: '🏥' },
        { label: 'Transport', value: 'Bhanwarkuan', color: 'bg-orange-50 border-orange-200 text-orange-700', icon: '🚌' },
        { label: 'Water', value: 'Bhanwarkuan', color: 'bg-blue-50 border-blue-200 text-blue-700', icon: '💧' },
      ],
    };
  }

  // Population
  if (/population|people|residents|how many/.test(q)) {
    return {
      text: `👥 **Population Data — Indore, Madhya Pradesh:**\n\n| Area | Population |\n|------|----------|\n| Rajwada | 25,000 |\n| Sarafa | 12,000 |\n| Old Palasia | 18,000 |\n| Vijay Nagar | 22,000 |\n| Bhanwarkuan | 15,000 |\n| **Total (demo scope)** | **92,000** |\n\nBhanwarkuan has the **highest vulnerability index (0.74)** despite not being the largest area, due to a high child dependency ratio (38%) and elderly population (21%).`,
    };
  }

  // Default fallback
  const randomTip = CIVIC_KB.tips[Math.floor(Math.random() * CIVIC_KB.tips.length)];
  return {
    text: `I'm not sure I understood that exactly, but here's something useful:\n\n💡 **Tip:** ${randomTip}\n\nTry asking me things like:\n• "What are the top civic issues?"\n• "Tell me about Vijay Nagar"\n• "How do I earn civic points?"\n• "What is a civic desert?"\n• "Show me investment recommendations"`,
  };
}

// ─── Typing Animation ─────────────────────────────────────────────────────────

function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0, 1, 2].map(i => (
        <div
          key={i}
          className="w-2 h-2 rounded-full bg-blue-400 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

// ─── Message Bubble ───────────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: Message }) {
  const isBot = msg.role === 'assistant';

  // Parse markdown-like bold: **text**
  const renderText = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className={cn('flex gap-3', isBot ? 'items-start' : 'items-start flex-row-reverse')}>
      {/* Avatar */}
      <div className={cn(
        'w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5',
        isBot ? 'bg-gradient-to-br from-blue-600 to-indigo-600' : 'bg-slate-700'
      )}>
        {isBot ? <Bot className="w-4 h-4 text-white" /> : <User className="w-4 h-4 text-white" />}
      </div>

      {/* Content */}
      <div className={cn('flex flex-col gap-2 max-w-[85%]', isBot ? 'items-start' : 'items-end')}>
        <div className={cn(
          'rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-line',
          isBot
            ? 'bg-white border border-slate-200 text-slate-800 shadow-sm rounded-tl-none'
            : 'bg-blue-600 text-white rounded-tr-none'
        )}>
          {msg.isTyping ? <TypingDots /> : <>{renderText(msg.text)}</>}
        </div>

        {/* Info cards */}
        {msg.cards && msg.cards.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {msg.cards.map((card, i) => (
              <div key={i} className={cn('flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-xs font-semibold', card.color)}>
                <span>{card.icon}</span>
                <span>{card.label}</span>
                <span className="opacity-60">·</span>
                <span>{card.value}</span>
              </div>
            ))}
          </div>
        )}

        <span className="text-[10px] text-slate-400 px-1">
          {msg.timestamp.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export const VoiceAssistantPage = () => {
  const { user } = useAuth();
  const { scoreState } = useCivicScore();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      text: `Hello${user?.name ? `, ${user.name.split(' ')[0]}` : ''}! 👋 I'm **CivicBot**, your AI voice assistant for CivicPulse Indore.\n\nI can help you explore civic data, understand accessibility scores, find critical issues, earn civic points, and navigate the platform.\n\nTry asking me something — or click one of the suggested questions below!`,
      timestamp: new Date(),
    },
  ]);

  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speakEnabled, setSpeakEnabled] = useState(true);
  const [contextData, setContextData] = useState<any>({});

  const recognitionRef = useRef<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isSupported = typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  // Load live data context
  useEffect(() => {
    Promise.all([
      fetchUnderservedRankings(5).catch(() => []),
      fetchMultiScaleAnalytics('Neighbourhood').catch(() => null),
    ]).then(([rankings, analytics]) => {
      setContextData({ rankings, analytics });
    });
  }, []);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const speak = useCallback((text: string) => {
    if (!speakEnabled || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const plain = text.replace(/\*\*/g, '').replace(/[#•→·]/g, '').replace(/\n+/g, '. ');
    const utterance = new SpeechSynthesisUtterance(plain.slice(0, 500));
    utterance.lang = 'en-IN';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, [speakEnabled]);

  const addMessage = (role: 'user' | 'assistant', text: string, cards?: QuickCard[]) => {
    const msg: Message = {
      id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
      role,
      text,
      timestamp: new Date(),
      cards,
    };
    setMessages(prev => [...prev, msg]);
    return msg;
  };

  const handleSend = useCallback(async (query: string) => {
    const q = query.trim();
    if (!q) return;

    setInputText('');
    addMessage('user', q);

    // Show typing indicator
    const typingId = `typing_${Date.now()}`;
    setMessages(prev => [...prev, {
      id: typingId,
      role: 'assistant',
      text: '',
      timestamp: new Date(),
      isTyping: true,
    }]);

    // Simulate thinking delay (400–900ms)
    await new Promise(r => setTimeout(r, 400 + Math.random() * 500));

    const { text, cards } = generateResponse(q, contextData, user);

    // Replace typing bubble with real response
    setMessages(prev => prev.map(m =>
      m.id === typingId ? { ...m, text, cards, isTyping: false } : m
    ));

    speak(text);
  }, [contextData, user, speak]);

  const handleVoiceInput = () => {
    if (!isSupported) return;

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SR();
    recognition.lang = 'en-IN';
    recognition.interimResults = false;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInputText(transcript);
      handleSend(transcript);
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  };

  const stopSpeaking = () => {
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
  };

  const clearChat = () => {
    setMessages([{
      id: 'welcome_reset',
      role: 'assistant',
      text: `Chat cleared! Ask me anything about CivicPulse Indore. 🏙️`,
      timestamp: new Date(),
    }]);
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 md:px-8 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-sm">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-lg font-bold text-slate-900 tracking-tight">CivicBot</h1>
                  <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Online
                  </span>
                </div>
                <p className="text-xs text-slate-400">AI Voice Assistant · CivicPulse Indore</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* TTS toggle */}
              <button
                onClick={() => { setSpeakEnabled(v => !v); stopSpeaking(); }}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition',
                  speakEnabled
                    ? 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100'
                    : 'bg-slate-100 border-slate-200 text-slate-500 hover:bg-slate-200'
                )}
                title={speakEnabled ? 'Disable voice output' : 'Enable voice output'}
              >
                {speakEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">{speakEnabled ? 'Voice On' : 'Voice Off'}</span>
              </button>

              {isSpeaking && (
                <button
                  onClick={stopSpeaking}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border bg-red-50 border-red-200 text-red-600 hover:bg-red-100 transition animate-pulse"
                >
                  <Square className="w-3.5 h-3.5" />
                  Stop
                </button>
              )}

              <button
                onClick={clearChat}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
                title="Clear chat"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 max-w-5xl mx-auto w-full px-4 md:px-8 py-4 flex flex-col gap-4">
        {/* Quick stats strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { icon: <Activity className="w-3.5 h-3.5" />, label: 'Active Issues', value: '4', color: 'text-red-600 bg-red-50 border-red-200' },
            { icon: <MapPin className="w-3.5 h-3.5" />, label: 'Civic Deserts', value: '2', color: 'text-orange-600 bg-orange-50 border-orange-200' },
            { icon: <Star className="w-3.5 h-3.5" />, label: 'Your Score', value: `${scoreState.totalScore}`, color: 'text-blue-600 bg-blue-50 border-blue-200' },
            { icon: <MessageSquare className="w-3.5 h-3.5" />, label: 'Messages', value: `${messages.length}`, color: 'text-slate-600 bg-slate-50 border-slate-200' },
          ].map(s => (
            <div key={s.label} className={cn('flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-semibold', s.color)}>
              {s.icon}
              <div>
                <div className="font-bold">{s.value}</div>
                <div className="font-normal opacity-75 text-[10px]">{s.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Chat messages */}
        <div className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col" style={{ minHeight: '400px', maxHeight: '55vh' }}>
          <div className="flex-1 overflow-y-auto p-4 space-y-5">
            {messages.map(msg => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-slate-100 p-3">
            <form
              onSubmit={e => { e.preventDefault(); handleSend(inputText); }}
              className="flex items-center gap-2"
            >
              <button
                type="button"
                onClick={handleVoiceInput}
                disabled={!isSupported}
                className={cn(
                  'w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition border',
                  isListening
                    ? 'bg-red-500 border-red-500 text-white animate-pulse'
                    : isSupported
                      ? 'bg-blue-50 border-blue-200 text-blue-600 hover:bg-blue-100'
                      : 'bg-slate-100 border-slate-200 text-slate-300 cursor-not-allowed'
                )}
                title={isListening ? 'Stop listening' : 'Speak your question'}
              >
                {isListening ? <Square className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>

              <input
                ref={inputRef}
                type="text"
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                placeholder={isListening ? 'Listening...' : 'Type or speak your question...'}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
              />

              <button
                type="submit"
                disabled={!inputText.trim()}
                className="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center shrink-0 transition disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>

        {/* Suggested questions */}
        <div>
          <p className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-blue-400" />
            Suggested questions — click to ask
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map(q => (
              <button
                key={q}
                onClick={() => handleSend(q)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 hover:border-blue-400 hover:bg-blue-50 text-xs text-slate-600 hover:text-blue-700 font-medium rounded-xl transition shadow-sm"
              >
                <ChevronRight className="w-3 h-3 opacity-50" />
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
