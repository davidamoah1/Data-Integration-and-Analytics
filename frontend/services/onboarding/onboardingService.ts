import { apiClient } from '../api/client';

export interface OnboardingStepData {
  key: string;
  title: string;
  description: string;
  href: string;
  icon: string;
  optional: boolean;
  action_label: string;
}

export interface OnboardingFlowData {
  role: string;
  title: string;
  description: string;
  steps: OnboardingStepData[];
}

export interface OnboardingStatus {
  flow: OnboardingFlowData;
  completed_steps: string[];
  current_step_index: number;
  current_step: string | null;
  total_steps: number;
  completed_count: number;
  percentage: number;
  is_complete: boolean;
  skipped: boolean;
}

export interface OnboardingNextAction {
  step_key: string;
  title: string;
  description: string;
  href: string;
  icon: string;
  action_label: string;
}

export const onboardingService = {
  async getStatus(): Promise<OnboardingStatus> {
    return apiClient.get<OnboardingStatus>('/api/onboarding/status');
  },

  async completeStep(stepKey: string): Promise<OnboardingStatus> {
    return apiClient.post<OnboardingStatus>('/api/onboarding/complete', {
      step_key: stepKey,
    });
  },

  async skipOnboarding(): Promise<{ skipped: boolean }> {
    return apiClient.post<{ skipped: boolean }>('/api/onboarding/skip');
  },

  async resetOnboarding(): Promise<OnboardingStatus> {
    return apiClient.post<OnboardingStatus>('/api/onboarding/reset');
  },

  async getNextAction(): Promise<OnboardingNextAction | null> {
    return apiClient.get<OnboardingNextAction | null>('/api/onboarding/next-action');
  },
};
