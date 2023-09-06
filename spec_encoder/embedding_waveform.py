import torch
import torch.nn as nn



class Waveform_encoder(nn.Module):
     
     def __init__(self,num_wav_size,hidden_state,output_dim,device) -> None:
          super().__init__()
          self.linear = nn.Linear(num_wav_size, hidden_state)
          
          ##First layer transformer
          self.encoder_layer = nn.TransformerEncoderLayer(d_model=512, nhead=8)
          self.transformer_encoder = nn.TransformerEncoder(self.encoder_layer, num_layers=6)
          self.decoder_layer = nn.TransformerDecoderLayer(d_model=512, nhead=8)
          self.transformer_decoder = nn.TransformerDecoder(self.decoder_layer, num_layers=6)
          
          ##Second  layer transformer
          self.second_encoder_layer = nn.TransformerEncoderLayer(d_model=512, nhead=8)
          self.second_transformer_encoder = nn.TransformerEncoder(self.encoder_layer, num_layers=6)
          self.second_decoder_layer = nn.TransformerDecoderLayer(d_model=512, nhead=8)
          self.second_transformer_decoder = nn.TransformerDecoder(self.decoder_layer, num_layers=6)
          
          self.device = device
          self.output_layer = nn.Linear(hidden_state,output_dim)
          
          self.adaptive_avg_pool = nn.AdaptiveAvgPool2d((1, output_dim))
          self.output_layer_pooling = nn.Linear(output_dim,output_dim)
          
     def forward(self,waveform):
          
          first_encoding = []
          
          for var in waveform:
               embedding = self.linear(waveform[var])
               PE = self.positional_encoding(len(waveform[var]))
               embedding = embedding + PE
               encoder_out = self.transformer_encoder(embedding.unsqueeze(1))
               decoder_out = self.transformer_decoder(embedding.unsqueeze(1),encoder_out)
               
               first_encoding.append(decoder_out.squeeze(1))
          
          
          ##Second layer Transformer
          
          decoding = []
          for i in range(len(first_encoding[0])):
               second_encoding = []
               for j in range(len(first_encoding)):
                    second_encoding.append(first_encoding[j][i])
               stacked_eccoding_2 = torch.stack(second_encoding)
               encoder_out_2 = self.second_transformer_encoder(stacked_eccoding_2.unsqueeze(1))
               decoder_out_2 = self.second_transformer_decoder(stacked_eccoding_2.unsqueeze(1),
                                                       encoder_out_2)
               decoding.append(decoder_out_2.squeeze(1))

          decoding_reshape = []
          for i in range(len(decoding[0])):
               new_tensor_rows = [decoding[j][i] for j in range(len(decoding))]
               new_tensor = torch.stack(new_tensor_rows)
               decoding_reshape.append(new_tensor)

          outputs = []
          for i in range(len(decoding_reshape)):
               output = self.output_layer(decoding_reshape[i])
               output_pooling = self.adaptive_avg_pool(output.unsqueeze(0).unsqueeze(0))
               final_output = self.output_layer_pooling(output_pooling.squeeze(0).squeeze(0))
               outputs.append(final_output)
          return outputs

     def positional_encoding(self, max_sequence_length):
          
          PE = torch.zeros(max_sequence_length, 512).to(self.device)
          position = torch.arange(0, max_sequence_length).unsqueeze(1).to(self.device) #shape(max_sequence_len, 1) 转为二维，方便后面直接相乘
          buff = torch.pow(1 / 10000, 2*torch.arange(0, 512/2)
                                   /512).to(self.device)  # embedding_dimension/2
          PE[:, ::2] = torch.sin(position * buff)
          PE[:, 1::2] = torch.cos(position * buff)
          
          return PE
          
