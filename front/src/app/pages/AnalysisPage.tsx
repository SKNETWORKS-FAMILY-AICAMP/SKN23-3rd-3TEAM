import { Link } from "react-router";
import { motion } from "motion/react";
import { useState, useEffect } from "react";
import { Icon } from "../components/ui/icon";
import { Loading } from "@/app/components/ui/loading";
import { fetchAnalysisHistory, fetchFactorials, type AnalysisResult, type KeywordResponse } from "@/app/api/analysisApi";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Legend } from "recharts";
import { Calendar, ScanFace, TrendingUp, TrendingDown, Minus } from "lucide-react";

const factorialImages = import.meta.glob<string>(
  '../../assets/factorial/*.svg',
  { eager: true, query: '?url', import: 'default' },
);

// UI 전용 설정
const SKIN_METRICS = [
  { key: "moisture",     label: "수분",     icon: "moisture" as const,      color: "#4e76ba" },
  { key: "elasticity",   label: "탄력",     icon: "elasticity" as const,    color: "#6cb78e" },
  { key: "wrinkle",      label: "주름",     icon: "wrinkle" as const,       color: "#f6b483" },
  { key: "pore",         label: "모공",     icon: "pore" as const,          color: "#8959a2" },
  { key: "pigmentation", label: "색소침착", icon: "pigmentation" as const,  color: "#cc528e" },
];

function MetricBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 1, ease: "easeOut", delay: 0.3 }}
        className="h-full rounded-full"
        style={{ background: color }}
      />
    </div>
  );
}

function ScoreGauge({ score }: { score: number }) {
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="relative w-100 h-auto">
      <svg className="w-full h-full -rotate-90" viewBox="-7 -7 134 134">
        <circle cx="60" cy="60" r="54" fill="none" stroke="#E5E7EB" strokeWidth="13" />
        <motion.circle
          cx="60" cy="60" r="54"
          fill="none"
          stroke="url(#scoreGradient)"
          strokeWidth="13"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
        />
        <defs>
          <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#84C13D" />
            <stop offset="100%" stopColor="#A8D870" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-4xl font-bold text-[#84C13D]"
        >
          {score}
        </motion.span>
        <span className="text-xs text-gray-400 font-medium">전체 점수</span>
      </div>
    </div>
  );
}

/** ISO 날짜 문자열 → "YYYY.MM.DD" */
function fmtDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

export function AnalysisPage() {
  const [activeTab, setActiveTab]             = useState<"current" | "compare">("current");
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResult[]>([]);
  const [selectedIndex, setSelectedIndex]     = useState(0);
  const [isLoading, setIsLoading]             = useState(true);
  const [hasNoData, setHasNoData]             = useState(false);
  const [factorialList, setFactorialList]     = useState<KeywordResponse[]>([]);

  useEffect(() => {
    fetchFactorials()
      .then(setFactorialList)
      .catch((err: Error) => console.error("팩토리얼 키워드 목록 조회 실패:", err));
  }, []);

  useEffect(() => {
    fetchAnalysisHistory()
      .then((data) => {
        if (data.length === 0) {
          setHasNoData(true);
        } else {
          setAnalysisHistory(data);
        }
      })
      .catch(() => setHasNoData(true))
      .finally(() => setIsLoading(false));
  }, []);

  // ── 선택된 분석 & 바로 이전 분석 ──────────────────────────────
  const currentAnalysis  = analysisHistory[selectedIndex]     ?? null;
  const previousAnalysis = analysisHistory[selectedIndex + 1] ?? null;

  const analysisDate = currentAnalysis  ? fmtDate(currentAnalysis.created_at)  : "";
  const previousDate = previousAnalysis ? fmtDate(previousAnalysis.created_at) : "";

  // ── 공통 헬퍼 ─────────────────────────────────────────────────
  const extractNum = (raw: unknown, fallback: number): number => {
    if (typeof raw === "number") return raw;
    if (raw && typeof raw === "object" && "score" in raw)
      return Number((raw as { score: unknown }).score) || fallback;
    return fallback;
  };
  const extractStr = (raw: unknown, fallback: string): string => {
    if (typeof raw === "string") return raw;
    if (raw && typeof raw === "object" && "label" in raw)
      return String((raw as { label: unknown }).label) || fallback;
    return fallback;
  };

  // ── 현재 분석 지표 ─────────────────────────────────────────────
  const ad    = currentAnalysis?.analysis_data ?? {};
  const apiM  = (ad.metrics ?? {}) as Record<string, unknown>;

  const overallScore  = extractNum(ad.overall_score, 0);
  const skinType      = extractStr(ad.skin_type,     "");
  const skinTypeDesc  = extractStr(ad.skin_type_detail, "");
  const factorial     = ad?.factorial;
  const analysisImage = currentAnalysis?.image_url?.[0] ?? "";

  const skinMetrics = SKIN_METRICS.map((m) => {
    const raw = apiM[m.key];
    return { ...m, value: extractNum(raw, 0), desc: extractStr(raw, "") };
  });

  // ── 이전 분석 지표 ─────────────────────────────────────────────
  const prevAd   = previousAnalysis?.analysis_data ?? {};
  const prevApiM = (prevAd.metrics ?? {}) as Record<string, unknown>;

  const prevOverallScore = extractNum(prevAd.overall_score, 0);
  const prevSkinMetrics  = SKIN_METRICS.map((m) => {
    const raw = prevApiM[m.key];
    return { ...m, value: extractNum(raw, 0), desc: extractStr(raw, "") };
  });

  // ── 레이더 차트 데이터 ─────────────────────────────────────────
  const getVal = (list: typeof skinMetrics, key: string) =>
    list.find((m) => m.key === key)?.value ?? 0;

  const radarData = [
    { subject: "수분",     A: getVal(skinMetrics, "moisture")     },
    { subject: "탄력",     A: getVal(skinMetrics, "elasticity")   },
    { subject: "주름",     A: getVal(skinMetrics, "wrinkle")      },
    { subject: "모공",     A: getVal(skinMetrics, "pore")         },
    { subject: "색소침착", A: getVal(skinMetrics, "pigmentation") },
  ];

  const compareRadarData = [
    { subject: "수분",     A: getVal(skinMetrics, "moisture"),     B: getVal(prevSkinMetrics, "moisture")     },
    { subject: "탄력",     A: getVal(skinMetrics, "elasticity"),   B: getVal(prevSkinMetrics, "elasticity")   },
    { subject: "주름",     A: getVal(skinMetrics, "wrinkle"),      B: getVal(prevSkinMetrics, "wrinkle")      },
    { subject: "모공",     A: getVal(skinMetrics, "pore"),         B: getVal(prevSkinMetrics, "pore")         },
    { subject: "색소침착", A: getVal(skinMetrics, "pigmentation"), B: getVal(prevSkinMetrics, "pigmentation") },
  ];

  // ── 로딩 / 빈 상태 ────────────────────────────────────────────
  if (isLoading) return <Loading className="mt-34" />;

  if (hasNoData) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-[#F8FBF3] px-6 text-center">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" style={{ background: "#E8F5D0" }}>
          <ScanFace className="w-8 h-8" style={{ color: "#84C13D" }} />
        </div>
        <h2 className="text-base font-bold text-gray-800 mb-2">아직 피부 분석 결과가 없어요</h2>
        <p className="text-sm text-gray-500 leading-relaxed mb-6">
          채팅에서 피부 이미지를 업로드하면<br />AI가 분석 결과를 저장해 드려요
        </p>
        <Link
          to="/chat"
          className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white transition-all"
          style={{ background: "#84C13D", boxShadow: "0 2px 8px rgba(133,193,61,0.35)" }}
        >
          채팅으로 분석 시작하기
        </Link>
      </div>
    );
  }

  const scoreDelta = overallScore - prevOverallScore;

  return (
    <div className="h-full overflow-y-auto bg-[#F8FBF3]">
      <div className="max-w-5xl mx-auto px-4 py-6">

        {/* ── 헤더 ─────────────────────────────────────────────── */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-gray-900 font-bold">피부 분석 결과</h1>
            <p className="text-sm text-gray-500 mt-0.5">AI가 분석한 나의 피부 상태</p>
          </div>
          {/* 4차 작업때 날짜 변경 기능 사용시 활성화 */}
          {/* <div className="flex items-center gap-2 bg-white rounded-xl px-3 py-2 border border-gray-100 shadow-sm">
            <button
              className="p-1 transition-colors disabled:opacity-30 disabled:cursor-not-allowed hover:text-[#84C13D]"
              onClick={() => setSelectedIndex((i) => Math.min(analysisHistory.length - 1, i + 1))}
              disabled={selectedIndex >= analysisHistory.length - 1}
            >
              <ChevronLeft className="w-4 h-4 text-gray-400" />
            </button>
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" style={{ color: "#84C13D" }} />
              <span className="text-xs font-medium text-gray-700">{analysisDate}</span>
            </div>
            <button
              className="p-1 transition-colors disabled:opacity-30 disabled:cursor-not-allowed hover:text-[#84C13D]"
              onClick={() => setSelectedIndex((i) => Math.max(0, i - 1))}
              disabled={selectedIndex === 0}
            >
              <ChevronRight className="w-4 h-4 text-gray-400" />
            </button>
          </div> */}
        </div>

        {/* ── 탭 ──────────────────────────────────────────────── */}
        <div className="flex gap-1 bg-white rounded-xl p-1 border border-gray-100 shadow-sm mb-6 w-fit">
          {[{ id: "current", label: "현재 분석" }, { id: "compare", label: "비교 분석" }].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as "current" | "compare")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeTab === tab.id ? "text-white shadow-sm" : "text-gray-500 hover:text-gray-700"
              }`}
              style={activeTab === tab.id ? { background: "#84C13D" } : {}}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ════════════════════════════════════════════════════════
            현재 분석 탭
        ════════════════════════════════════════════════════════ */}
        {activeTab === "current" ? (
          <div className="space-y-5">

            {/* 점수 + 피부 타입 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm aspect-square overflow-auto"
              >
                <h3 className="font-semibold text-gray-800 mb-4">종합 피부 점수</h3>
                <div className="flex items-center gap-6 mb-6">
                  <ScoreGauge score={overallScore} />
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2.5 py-1 rounded-lg text-xs font-semibold text-white bg-[#84C13D]">{skinType}</span>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed">{skinTypeDesc}</p>
                  </div>
                </div>
                <>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="px-2.5 py-1 rounded-lg text-xs font-semibold text-white bg-[#84C13D]">추천 관리법</span>
                  </div>
                  <div className="flex items-start gap-3">
                    {factorial?.map((keyword) => {
                      const item   = factorialList.find((f) => f.label === keyword);
                      const imgSrc = factorialImages[`../../assets/factorial/${item?.keyword}.svg`];
                      
                      return (
                        <div key={keyword} className="flex flex-col items-center gap-1">
                          {imgSrc && (
                            <img src={imgSrc} alt={item?.label ?? keyword} className="w-18 h-18 object-contain" />
                          )}
                          <span className="w-18 text-[13px] text-gray-500 text-center font-medium leading-tight break-keep">
                            {item?.label ?? keyword}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </>
              </motion.div>

              {/* 분석 이미지 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden aspect-square"
              >
                <div className="relative h-full">
                  {analysisImage ? (
                    <img src={analysisImage} alt="Skin analysis" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                      <ScanFace className="w-12 h-12 text-gray-300" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  <div className="absolute bottom-4 left-4 right-4">
                    <p className="text-white text-sm font-medium">분석 이미지</p>
                    <p className="text-white/70 text-xs">{analysisDate} 분석</p>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* 피부 지표 상세 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
            >
              <h3 className="font-semibold text-gray-800 mb-5">피부 지표 상세</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {skinMetrics.map((metric, idx) => {
                  return (
                    <motion.div
                      key={metric.key}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 + idx * 0.08 }}
                      className="flex items-start gap-3 p-3 rounded-xl bg-gray-50"
                    >
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                        style={{ background: metric.color + "20" }}
                      >
                        <Icon name={metric.icon} size={20} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-700">{metric.label}</span>
                          <span className="text-sm font-bold" style={{ color: metric.color }}>
                            {metric.value}
                          </span>
                        </div>
                        <MetricBar value={metric.value} color={metric.color} />
                        <p className="text-[11px] text-gray-400 mt-1">{metric.desc}</p>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>

            {/* 레이더 차트 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
            >
              <h3 className="font-semibold text-gray-800 mb-1">피부 레이더 차트</h3>
              <p className="text-xs text-gray-400 mb-4">현재 피부 상태 종합</p>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
                  <PolarGrid stroke="#E5E7EB" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <Radar name="현재" dataKey="A" stroke="#84C13D" fill="#84C13D" fillOpacity={0.3} />
                  <Legend formatter={(value) => <span className="text-xs text-gray-600">{value}</span>} />
                </RadarChart>
              </ResponsiveContainer>
            </motion.div>

          </div>

        ) : (
        /* ════════════════════════════════════════════════════════
            비교 분석 탭
        ════════════════════════════════════════════════════════ */
          analysisHistory.length < 2 ? (
            /* 기록이 1개뿐일 때 */
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center py-20 text-center"
            >
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4" style={{ background: "#E8F5D0" }}>
                <Calendar className="w-7 h-7" style={{ color: "#84C13D" }} />
              </div>
              <h3 className="text-sm font-bold text-gray-700 mb-1">비교 분석 준비 중</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                분석 기록이 2회 이상 쌓이면<br />변화 추이를 비교할 수 있어요
              </p>
            </motion.div>

          ) : (
            /* 기록이 2개 이상일 때 */
            <div className="space-y-5">

              {/* 피부 점수 변화 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
              >
                <h3 className="font-semibold text-gray-800 mb-5">피부 점수 변화</h3>
                <div className="flex items-center gap-4">

                  {/* 이전 점수 */}
                  <div className="flex-1 text-center py-5 rounded-2xl bg-gray-50">
                    <p className="text-xs text-gray-400 mb-2">{previousDate}</p>
                    <p className="text-5xl font-bold text-gray-400">{prevOverallScore}</p>
                    <p className="text-xs text-gray-400 mt-2 font-medium">이전</p>
                  </div>

                  {/* 변화량 */}
                  <div className="flex flex-col items-center gap-1.5 px-2">
                    {scoreDelta > 0 ? (
                      <TrendingUp className="w-6 h-6 text-green-500" />
                    ) : scoreDelta < 0 ? (
                      <TrendingDown className="w-6 h-6 text-red-400" />
                    ) : (
                      <Minus className="w-6 h-6 text-gray-400" />
                    )}
                    <span
                      className={`text-base font-bold ${
                        scoreDelta > 0 ? "text-green-500" : scoreDelta < 0 ? "text-red-400" : "text-gray-400"
                      }`}
                    >
                      {scoreDelta > 0 ? `+${scoreDelta}` : scoreDelta}
                    </span>
                  </div>

                  {/* 현재 점수 */}
                  <div className="flex-1 text-center py-5 rounded-2xl" style={{ background: "#F0FAE4" }}>
                    <p className="text-xs text-gray-400 mb-2">{analysisDate}</p>
                    <p className="text-5xl font-bold" style={{ color: "#84C13D" }}>{overallScore}</p>
                    <p className="text-xs text-gray-400 mt-2 font-medium">현재</p>
                  </div>

                </div>
              </motion.div>

              {/* 지표별 변화 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
                className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
              >
                <h3 className="font-semibold text-gray-800 mb-4">지표별 변화</h3>
                <div className="space-y-3">
                  {skinMetrics.map((metric, idx) => {
                    const prevVal = prevSkinMetrics.find((m) => m.key === metric.key)?.value ?? 0;
                    const delta   = metric.value - prevVal;
                    return (
                      <motion.div
                        key={metric.key}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.15 + idx * 0.06 }}
                        className="flex items-center gap-3 p-3 rounded-xl bg-gray-50"
                      >
                        <div
                          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                          style={{ background: metric.color + "20" }}
                        >
                          <Icon name={metric.icon} size={16} />
                        </div>
                        <span className="flex-1 text-sm font-medium text-gray-700">{metric.label}</span>
                        {/* 이전 → 현재 값 */}
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-gray-400 font-medium">{prevVal}</span>
                          <span className="text-gray-300 text-xs">→</span>
                          <span className="font-semibold" style={{ color: metric.color }}>{metric.value}</span>
                        </div>
                        {/* 변화량 */}
                        <div
                          className={`flex items-center gap-0.5 text-xs font-bold w-12 justify-end ${
                            delta > 0 ? "text-green-500" : delta < 0 ? "text-red-400" : "text-gray-400"
                          }`}
                        >
                          {delta > 0 ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : delta < 0 ? (
                            <TrendingDown className="w-3 h-3" />
                          ) : (
                            <Minus className="w-3 h-3" />
                          )}
                          <span className="ml-0.5">
                            {delta > 0 ? `+${delta}` : delta === 0 ? "0" : delta}
                          </span>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </motion.div>

              {/* 레이더 차트 오버레이 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.2 }}
                className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
              >
                <h3 className="font-semibold text-gray-800 mb-1">피부 레이더 비교</h3>
                <p className="text-xs text-gray-400 mb-4">
                  현재({analysisDate}) vs 이전({previousDate}) 피부 상태 비교
                </p>
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={compareRadarData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
                    <PolarGrid stroke="#E5E7EB" />
                    <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: "#6B7280" }} />
                    <Radar
                      name="이전"
                      dataKey="B"
                      stroke="#9CA3AF"
                      fill="#9CA3AF"
                      fillOpacity={0.15}
                      strokeDasharray="5 3"
                    />
                    <Radar
                      name="현재"
                      dataKey="A"
                      stroke="#84C13D"
                      fill="#84C13D"
                      fillOpacity={0.35}
                    />
                    <Legend formatter={(value) => <span className="text-xs text-gray-600">{value}</span>} />
                  </RadarChart>
                </ResponsiveContainer>
              </motion.div>

            </div>
          )
        )}

      </div>
    </div>
  );
}
