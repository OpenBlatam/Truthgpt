"""
TruthGPT GPU Submodule

CUDA GPU acceleration routines.
"""
module GPU

export attention_cuda, has_cuda

const CUDA_AVAILABLE = Ref(false)

function __init__()
    try
        @eval using CUDA
        CUDA_AVAILABLE[] = CUDA.functional()
    catch
        CUDA_AVAILABLE[] = false
    end
end

has_cuda() = CUDA_AVAILABLE[]

function attention_cuda(Q, K, V; scale=nothing)
    if !has_cuda()
        error("CUDA not available. Install CUDA.jl: using Pkg; Pkg.add(\"CUDA\")")
    end
    
    @eval begin
        using CUDA
        
        Q_gpu = CUDA.CuArray(Q)
        K_gpu = CUDA.CuArray(K)
        V_gpu = CUDA.CuArray(V)
        
        scale_val = isnothing($scale) ? 1.0f0 / sqrt(Float32(size(Q, 4))) : $scale
        
        scores = batched_mul_cuda(Q_gpu, permutedims(K_gpu, (1, 2, 4, 3))) .* scale_val
        
        scores_max = maximum(scores, dims=4)
        exp_scores = CUDA.exp.(scores .- scores_max)
        weights = exp_scores ./ sum(exp_scores, dims=4)
        
        output_gpu = batched_mul_cuda(weights, V_gpu)
        
        return Array(output_gpu)
    end
end

function batched_mul_cuda(A, B)
    @eval begin
        using CUDA
        batch, heads = size(A, 1), size(A, 2)
        m, k = size(A, 3), size(A, 4)
        _, n = size(B, 3), size(B, 4)
        
        C = CUDA.zeros(eltype(A), batch, heads, m, n)
        
        for b in 1:batch, h in 1:heads
            CUDA.CUBLAS.gemm!('N', 'N', 1.0f0, A[b,h,:,:], B[b,h,:,:], 0.0f0, view(C, b, h, :, :))
        end
        
        return C
    end
end

end # module GPU
