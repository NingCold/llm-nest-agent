/// Per-AI model settings. Unset fields use the existing automatic generation policy.
#[derive(Debug, Clone, Copy, Default)]
pub struct Parameters {
    pub temperature: Option<f32>,
    pub max_tokens: Option<u32>,
}

use crate::Result;
use ai_client::{ResolvedSelection, generation::GenerationLimits};
use common::GenerationOptions;

/// Local admission estimate, not provider usage: complete assembled input plus
/// the configured output ceiling (which already includes required thinking).
pub fn request_budget(messages: &[common::Message], output_tokens: u32) -> u64 {
    messages
        .iter()
        .map(|message| u64::from(crate::consciousness::estimate(message)))
        .sum::<u64>()
        + u64::from(output_tokens)
}

/// Reserve at least one input token; the consciousness service checks the actual prompt.
pub fn limits(resolved: &ResolvedSelection) -> GenerationLimits {
    let mut limits = resolved.generation_limits();
    let context_max = resolved
        .spec
        .context_window
        .unwrap_or(8192)
        .saturating_sub(1);
    limits.max_output_tokens = Some(
        limits
            .max_output_tokens
            .unwrap_or(context_max)
            .min(context_max),
    );
    limits
}

#[cfg(test)]
mod tests {
    use super::*;
    use ai_client::{
        ModelSelection, ModelSpec, Protocol, ReasoningCapability, ReasoningEffort, ReasoningFormat,
    };

    #[test]
    fn request_budget_tracks_assembled_input_and_output_ceiling() {
        let messages = vec![common::Message::new(
            common::Role::User,
            vec![common::ContentPart::Text("你好".into())],
        )];
        assert_eq!(request_budget(&messages, 1024), 6 + 16 + 1024);
        assert_eq!(request_budget(&messages, 5120), 6 + 16 + 5120);
        let mut longer = messages.clone();
        longer.extend(messages);
        assert_eq!(request_budget(&longer, 1024), 2 * (6 + 16) + 1024);
    }

    #[test]
    fn independent_defaults_and_explicit_caps_use_the_same_context_budget() {
        let mut resolved = ResolvedSelection {
            selection: ModelSelection {
                provider: "test".into(),
                model: "model".into(),
                reasoning_effort: None,
            },
            spec: ModelSpec {
                image_input: Default::default(),
                id: "model".into(),
                wire: "wire".into(),
                display_name: "Model".into(),
                context_window: Some(8192),
                max_tokens: Some(6000),
                protocol: Protocol::OpenAIChat,
                reasoning: None,
            },
        };
        let mut binding = Parameters {
            temperature: None,
            max_tokens: None,
        };
        let defaults = options(&binding, &resolved).unwrap();
        assert_eq!(defaults.temperature, None);
        assert_eq!(defaults.max_tokens, Some(1024));
        binding.temperature = Some(0.3);
        binding.max_tokens = Some(4096);
        let explicit = options(&binding, &resolved).unwrap();
        assert_eq!(explicit.temperature, Some(0.3));
        assert_eq!(explicit.max_tokens, Some(4096));
        binding.max_tokens = Some(6001);
        assert!(options(&binding, &resolved).is_err());
        resolved.spec.max_tokens = None;
        binding.max_tokens = Some(8192);
        assert!(options(&binding, &resolved).is_err());
        resolved.spec.protocol = Protocol::Anthropic;
        resolved.spec.reasoning = Some(ReasoningCapability {
            format: ReasoningFormat::AnthropicThinking,
            levels: vec![ReasoningEffort::Medium],
            budget_tokens: None,
        });
        resolved.selection.reasoning_effort = Some(ReasoningEffort::Medium);
        binding.temperature = None;
        binding.max_tokens = None;
        let thinking = options(&binding, &resolved).unwrap();
        assert_eq!(thinking.max_tokens, Some(5120));
        assert_eq!(request_budget(&[], thinking.max_tokens.unwrap()), 5120);
        binding.max_tokens = Some(4096);
        assert!(options(&binding, &resolved).is_err());
    }
}

pub fn options(binding: &Parameters, resolved: &ResolvedSelection) -> Result<GenerationOptions> {
    let limits = limits(resolved);
    let max = limits
        .max_output_tokens
        .expect("social context has a finite budget");
    let answer_budget = 1024.min(resolved.spec.context_window.unwrap_or(8192) / 4);
    let automatic = (limits.min_output_tokens - 1)
        .saturating_add(answer_budget)
        .min(max);
    let options = GenerationOptions {
        temperature: binding.temperature,
        max_tokens: Some(binding.max_tokens.unwrap_or(automatic)),
        stream: true,
        ..Default::default()
    };
    resolved.validate_generation(&options)?;
    if options.max_tokens.expect("output budget allocated") > max {
        return Err(crate::AgentError::Invalid(format!(
            "输出上限必须小于上下文窗口，当前最多 {max}"
        )));
    }
    Ok(options)
}
