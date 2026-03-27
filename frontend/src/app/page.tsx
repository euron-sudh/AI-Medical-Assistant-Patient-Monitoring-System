import Link from "next/link";
import Image from "next/image";
import {
  Stethoscope,
  FileText,
  Activity,
  Video,
  Mic,
  ShieldCheck,
  UserCheck,
  ClipboardList,
  TestTube,
  Upload,
  Brain,
  HeartPulse,
  ArrowRight,
  Star,
  CheckCircle,
  Users,
  Clock,
  Shield,
} from "lucide-react";

/* ─── Hero Section ────────────────────────────────────────────────────────── */

function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-20 left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-300 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-400 rounded-full blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:py-40">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          {/* Left: Text content */}
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-sm backdrop-blur-sm">
              <HeartPulse className="h-4 w-4" />
              AI-Powered Healthcare Platform
            </div>

            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl leading-tight">
              AI-Powered Medical Assistant{" "}
              <span className="text-blue-200">for Modern Healthcare</span>
            </h1>

            <p className="mt-6 max-w-xl text-lg text-blue-100 sm:text-xl leading-relaxed">
              MedAssist AI combines specialized AI doctors, real-time patient monitoring,
              and intelligent diagnostics to deliver accurate, instant medical insights.
            </p>

            <div className="mt-10 flex flex-col gap-4 sm:flex-row">
              <Link
                href="/register"
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-blue-700 shadow-lg transition hover:bg-blue-50 hover:shadow-xl"
              >
                Start Free Consultation
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/demo"
                className="inline-flex items-center justify-center gap-2 rounded-lg border-2 border-white/30 px-8 py-3.5 text-base font-semibold text-white backdrop-blur-sm transition hover:bg-white/10"
              >
                Watch Demo
              </Link>
            </div>

            {/* Trust badges */}
            <div className="mt-10 flex flex-wrap items-center gap-6 text-sm text-blue-200">
              <div className="flex items-center gap-1.5">
                <Shield className="h-4 w-4" />
                HIPAA Compliant
              </div>
              <div className="flex items-center gap-1.5">
                <Users className="h-4 w-4" />
                10,000+ Patients
              </div>
              <div className="flex items-center gap-1.5">
                <Clock className="h-4 w-4" />
                24/7 Monitoring
              </div>
            </div>
          </div>

          {/* Right: Hero image */}
          <div className="relative hidden lg:block">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl">
              <Image
                src="https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600&h=500&fit=crop&q=80"
                alt="Doctor using AI medical technology"
                width={600}
                height={500}
                className="rounded-2xl object-cover"
                priority
              />
              {/* Floating stat cards */}
              <div className="absolute bottom-4 left-4 rounded-xl bg-white/95 backdrop-blur-sm p-4 shadow-lg">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">98.5% Accuracy</p>
                    <p className="text-xs text-gray-500">AI Diagnostic Rate</p>
                  </div>
                </div>
              </div>
              <div className="absolute top-4 right-4 rounded-xl bg-white/95 backdrop-blur-sm p-4 shadow-lg">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
                    <Activity className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">Real-Time</p>
                    <p className="text-xs text-gray-500">Vitals Monitoring</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Wave divider */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 80h1440V30c-240 30-480 50-720 50S240 60 0 30v50z" fill="white" />
        </svg>
      </div>
    </section>
  );
}

/* ─── Stats Section ───────────────────────────────────────────────────────── */

function StatsSection() {
  const stats = [
    { value: "10,000+", label: "Patients Served" },
    { value: "50+", label: "AI Specialists" },
    { value: "98.5%", label: "Accuracy Rate" },
    { value: "<30s", label: "Response Time" },
  ];

  return (
    <section className="border-b border-gray-100 bg-white py-12">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid grid-cols-2 gap-8 lg:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-3xl font-bold text-blue-600 sm:text-4xl">
                {stat.value}
              </p>
              <p className="mt-1 text-sm text-gray-600">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Features Section (6 Cards) ──────────────────────────────────────────── */

const FEATURES = [
  {
    icon: Stethoscope,
    title: "AI Symptom Analysis",
    description:
      "Describe your symptoms and get instant AI-powered analysis from specialist AI doctors across 8+ medical specialties.",
    color: "text-blue-600 bg-blue-50 group-hover:bg-blue-100",
    image: "https://images.unsplash.com/photo-1666214280557-f1b5022eb634?w=400&h=250&fit=crop&q=80",
  },
  {
    icon: FileText,
    title: "Smart Report Reading",
    description:
      "Upload lab reports and get AI-interpreted results with automatic abnormality detection and plain-language explanations.",
    color: "text-emerald-600 bg-emerald-50 group-hover:bg-emerald-100",
    image: "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=400&h=250&fit=crop&q=80",
  },
  {
    icon: Activity,
    title: "Real-Time Monitoring",
    description:
      "24/7 vitals monitoring with intelligent anomaly detection, threshold alerts, and automatic doctor notifications.",
    color: "text-red-600 bg-red-50 group-hover:bg-red-100",
    image: "https://images.unsplash.com/photo-1551076805-e1869033e561?w=400&h=250&fit=crop&q=80",
  },
  {
    icon: Video,
    title: "Telemedicine",
    description:
      "Seamless video consultations with doctors when AI refers complex cases, with AI-generated session summaries.",
    color: "text-purple-600 bg-purple-50 group-hover:bg-purple-100",
    image: "https://images.unsplash.com/photo-1609220136736-443140cffec6?w=400&h=250&fit=crop&q=80",
  },
  {
    icon: Mic,
    title: "Voice Assistant",
    description:
      "Speak your symptoms naturally using voice interaction. AI transcribes, analyzes, and responds in real time.",
    color: "text-amber-600 bg-amber-50 group-hover:bg-amber-100",
    image: "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=400&h=250&fit=crop&q=80",
  },
  {
    icon: ShieldCheck,
    title: "Drug Safety",
    description:
      "Automatic drug interaction checking before any prescription. AI cross-references patient history and active medications.",
    color: "text-teal-600 bg-teal-50 group-hover:bg-teal-100",
    image: "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=400&h=250&fit=crop&q=80",
  },
];

function FeaturesSection() {
  return (
    <section id="features" className="bg-white py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-6">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
            Features
          </p>
          <h2 className="mt-2 text-3xl font-bold text-gray-900 sm:text-4xl">
            Everything You Need in One Platform
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-600">
            Six powerful capabilities working together to deliver comprehensive,
            AI-powered healthcare.
          </p>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="group overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm transition hover:shadow-xl hover:border-blue-100"
            >
              <div className="relative h-48 overflow-hidden">
                <Image
                  src={feature.image}
                  alt={feature.title}
                  width={400}
                  height={250}
                  className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                <div className={`absolute bottom-3 left-3 inline-flex rounded-lg p-2.5 ${feature.color} shadow-sm`}>
                  <feature.icon className="h-5 w-5" />
                </div>
              </div>
              <div className="p-6">
                <h3 className="text-xl font-semibold text-gray-900">
                  {feature.title}
                </h3>
                <p className="mt-3 text-gray-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── How It Works Section (Patient Journey Flow) ─────────────────────────── */

const STEPS = [
  { icon: UserCheck, title: "Select Specialty", description: "Choose your AI doctor type: General, Cardiology, Orthopedics, Neurology, and more." },
  { icon: ClipboardList, title: "Describe Symptoms", description: "AI specialist asks targeted questions to understand your condition in detail." },
  { icon: TestTube, title: "Get Test Recommendations", description: "AI suggests relevant medical tests based on your symptoms and history." },
  { icon: Upload, title: "Upload Reports", description: "Upload lab results or medical reports. AI reads and extracts structured data." },
  { icon: Brain, title: "AI Analysis", description: "AI reads reports, flags abnormalities, and correlates with your symptom profile." },
  { icon: HeartPulse, title: "Advice or Referral", description: "Minor cases get AI-guided advice. Serious cases are referred to a human doctor." },
];

function HowItWorksSection() {
  return (
    <section id="how-it-works" className="bg-gray-50 py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-6">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
            Patient Journey
          </p>
          <h2 className="mt-2 text-3xl font-bold text-gray-900 sm:text-4xl">
            How It Works
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-600">
            From symptoms to resolution — your complete patient journey, powered by AI.
          </p>
        </div>

        {/* Desktop: horizontal timeline */}
        <div className="mt-16 hidden lg:block">
          <div className="relative flex items-start justify-between">
            <div className="absolute top-10 left-[8%] right-[8%] h-0.5 bg-blue-200" />
            {STEPS.map((step, idx) => (
              <div key={step.title} className="relative flex w-1/6 flex-col items-center text-center px-2">
                <div className="relative z-10 flex h-20 w-20 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg ring-4 ring-blue-100">
                  <step.icon className="h-8 w-8" />
                </div>
                <span className="mt-3 inline-flex h-7 w-7 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
                  {idx + 1}
                </span>
                <h3 className="mt-3 text-sm font-semibold text-gray-900">{step.title}</h3>
                <p className="mt-2 text-xs text-gray-600 leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Mobile/Tablet: vertical timeline */}
        <div className="mt-12 space-y-8 lg:hidden">
          {STEPS.map((step, idx) => (
            <div key={step.title} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white shadow-md">
                  <step.icon className="h-5 w-5" />
                </div>
                {idx < STEPS.length - 1 && <div className="mt-2 h-full w-0.5 bg-blue-200" />}
              </div>
              <div className="pb-6">
                <span className="text-sm font-medium text-blue-600">Step {idx + 1}</span>
                <h3 className="mt-1 text-lg font-semibold text-gray-900">{step.title}</h3>
                <p className="mt-1 text-gray-600">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Testimonials ────────────────────────────────────────────────────────── */

function TestimonialsSection() {
  const testimonials = [
    {
      name: "Dr. Sarah Mitchell",
      role: "Cardiologist, NYC Health",
      image: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=80&h=80&fit=crop&q=80",
      quote: "MedAssist AI has revolutionized how I monitor my patients. The real-time alerts have helped catch critical events early.",
    },
    {
      name: "James Chen",
      role: "Patient",
      image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&q=80",
      quote: "I was able to get an AI analysis of my symptoms at 2 AM when no doctor was available. It correctly identified my condition.",
    },
    {
      name: "Dr. Priya Sharma",
      role: "Internal Medicine",
      image: "https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=80&h=80&fit=crop&q=80",
      quote: "The automated report reading saves me hours every week. AI catches abnormalities I might have overlooked in a busy clinic.",
    },
  ];

  return (
    <section className="bg-white py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-6">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Testimonials</p>
          <h2 className="mt-2 text-3xl font-bold text-gray-900 sm:text-4xl">Trusted by Doctors and Patients</h2>
        </div>

        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {testimonials.map((t) => (
            <div key={t.name} className="rounded-xl border border-gray-100 bg-white p-8 shadow-sm">
              <div className="flex gap-1 text-amber-400">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-current" />
                ))}
              </div>
              <p className="mt-4 text-gray-700 leading-relaxed italic">&ldquo;{t.quote}&rdquo;</p>
              <div className="mt-6 flex items-center gap-3">
                <Image src={t.image} alt={t.name} width={44} height={44} className="rounded-full object-cover" />
                <div>
                  <p className="text-sm font-semibold text-gray-900">{t.name}</p>
                  <p className="text-xs text-gray-500">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── CTA Banner ──────────────────────────────────────────────────────────── */

function CTABanner() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-r from-blue-600 to-indigo-700 py-16">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl" />
      </div>
      <div className="relative mx-auto max-w-4xl px-6 text-center">
        <h2 className="text-3xl font-bold text-white sm:text-4xl">
          Ready to Experience AI-Powered Healthcare?
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-lg text-blue-100">
          Join thousands of patients and doctors using MedAssist AI for smarter,
          faster, and more accurate healthcare.
        </p>
        <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-blue-700 shadow-lg transition hover:bg-blue-50 hover:shadow-xl"
          >
            Get Started Free
            <ArrowRight className="h-5 w-5" />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-lg border-2 border-white/30 px-8 py-3.5 text-base font-semibold text-white transition hover:bg-white/10"
          >
            Sign In
          </Link>
        </div>
      </div>
    </section>
  );
}

/* ─── Footer ──────────────────────────────────────────────────────────────── */

function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-2">
              <Image src="/images/logo.svg" alt="MedAssist AI" width={32} height={32} />
              <span className="text-lg font-bold text-white">MedAssist AI</span>
            </div>
            <p className="mt-3 text-sm leading-relaxed">
              Intelligent healthcare powered by specialized AI agents.
              Making quality medical insights accessible to everyone.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-white">Product</h3>
            <ul className="mt-4 space-y-2 text-sm">
              <li><Link href="/#features" className="hover:text-white transition">Features</Link></li>
              <li><Link href="/#how-it-works" className="hover:text-white transition">How it Works</Link></li>
              <li><Link href="/demo" className="hover:text-white transition">Demo</Link></li>
              <li><Link href="/register" className="hover:text-white transition">Pricing</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-white">Company</h3>
            <ul className="mt-4 space-y-2 text-sm">
              <li><Link href="#" className="hover:text-white transition">About</Link></li>
              <li><Link href="#" className="hover:text-white transition">Contact</Link></li>
              <li><Link href="#" className="hover:text-white transition">Careers</Link></li>
              <li><Link href="#" className="hover:text-white transition">Blog</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-white">Legal</h3>
            <ul className="mt-4 space-y-2 text-sm">
              <li><Link href="#" className="hover:text-white transition">Privacy Policy</Link></li>
              <li><Link href="#" className="hover:text-white transition">Terms of Service</Link></li>
              <li><Link href="#" className="hover:text-white transition">HIPAA Compliance</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-12 border-t border-gray-800 pt-8 text-center text-sm">
          <p>&copy; 2026 MedAssist AI. All rights reserved.</p>
          <p className="mt-1 text-gray-500">Built with AI for better healthcare.</p>
        </div>
      </div>
    </footer>
  );
}

/* ─── Main Landing Page ───────────────────────────────────────────────────── */

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      <nav className="absolute top-0 z-50 w-full">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/images/logo.svg" alt="MedAssist AI" width={36} height={36} />
            <span className="text-xl font-bold text-white">MedAssist AI</span>
          </Link>
          <div className="hidden items-center gap-6 sm:flex">
            <Link href="/#features" className="text-sm font-medium text-white/80 transition hover:text-white">Features</Link>
            <Link href="/#how-it-works" className="text-sm font-medium text-white/80 transition hover:text-white">How it Works</Link>
            <Link href="/demo" className="text-sm font-medium text-white/80 transition hover:text-white">Demo</Link>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="rounded-lg px-5 py-2 text-sm font-medium text-white transition hover:bg-white/10">
              Sign In
            </Link>
            <Link href="/register" className="rounded-lg bg-white px-5 py-2 text-sm font-medium text-blue-700 transition hover:bg-blue-50">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      <HeroSection />
      <StatsSection />
      <FeaturesSection />
      <HowItWorksSection />
      <TestimonialsSection />
      <CTABanner />
      <Footer />
    </main>
  );
}
