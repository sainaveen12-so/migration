import { useQuery, useMutation } from "@tanstack/react-query";
import { aiApi } from "@/lib/api";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useProjectStore } from "@/stores/project-store";

const PROVIDERS = [
  { id: "openai", name: "OpenAI", models: ["gpt-4o", "gpt-4o-mini"] },
  { id: "gemini", name: "Google Gemini", models: ["gemini-1.5-pro", "gemini-1.5-flash"] },
  { id: "claude", name: "Anthropic Claude", models: ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"] },
  { id: "ollama", name: "Ollama (Local)", models: ["llama3.2", "codellama", "mistral"] },
];

export function SettingsPage() {
  const { aiProvider, setAiProvider } = useProjectStore();

  const { data: providers } = useQuery({
    queryKey: ["ai-providers"],
    queryFn: async () => {
      const { data } = await aiApi.listProviders();
      return data;
    },
  });

  const switchMutation = useMutation({
    mutationFn: ({ provider, model }: { provider: string; model?: string }) =>
      aiApi.switchProvider(provider, model),
    onSuccess: (_, vars) => setAiProvider(vars.provider),
  });

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Settings" description="Configure AI providers and preferences" />
        <main className="flex-1 overflow-y-auto p-6">
          <Card>
            <CardHeader>
              <CardTitle>AI Provider</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4 text-sm text-gray-500">
                Current provider: <strong>{providers?.current || aiProvider}</strong>
              </p>
              <div className="grid gap-4 md:grid-cols-2">
                {PROVIDERS.map((provider) => (
                  <div
                    key={provider.id}
                    className={`rounded-lg border p-4 ${
                      aiProvider === provider.id ? "border-blue-500 bg-blue-50 dark:bg-blue-950" : "border-gray-200 dark:border-gray-800"
                    }`}
                  >
                    <h3 className="font-medium">{provider.name}</h3>
                    <div className="mt-2 space-y-1">
                      {provider.models.map((model) => (
                        <Button
                          key={model}
                          variant="outline"
                          size="sm"
                          className="mr-2"
                          onClick={() => switchMutation.mutate({ provider: provider.id, model })}
                        >
                          {model}
                        </Button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  );
}
