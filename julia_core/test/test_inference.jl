using Test
using TruthGPT.Inference

@testset "Inference & Sampling Tests" begin
    config = GenerationConfig(max_new_tokens=50, temperature=0.8f0, top_k=10, top_p=0.9f0)
    @test config.max_new_tokens == 50
    @test config.top_k == 10
    
    sampler = TokenSampler(42)
    logits = Float32[0.1, 0.5, 2.3, 0.8, 1.2]
    
    token_greedy = sample_greedy(logits)
    @test token_greedy == 3  # index of 2.3 (highest logit)
    
    token_topk = sample_topk(sampler, logits, 3)
    @test token_topk in [2, 3, 5]
    
    token_nucleus = sample_nucleus(sampler, logits, config)
    @test token_nucleus >= 1 && token_nucleus <= length(logits)
end
