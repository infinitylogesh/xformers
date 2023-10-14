ckpt_path="/home/ubuntu/codellama/"
hf_tokenizer="meta-llama/Llama-2-7b-hf"
batch_size=10
input_seq_len=1000
output_seq_len=400

python3 generate.py --ckpt_dir=$ckpt_path \
                    --batch_size=$batch_size \
                    --tokenizer_name=$hf_tokenizer \
                    --input_seq_len=$input_seq_len \
                    --output_seq_len=$output_seq_len
