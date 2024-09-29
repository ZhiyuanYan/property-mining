module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] m,
    output reg [10:0] x,
    output reg [10:0] n
);

    always @(posedge clk) begin
        if(rst)begin 
            x <= 0;
            m <= 0;
            n<=500;
        end else begin
            if(((x<n)))begin
                if(selector)begin
                x <= x + 1;
                m<= x;
                n<=n;
                end
                else begin
                    x<= x + 1;
                    m<= m;
                    n<=n;
                end
            end
            else begin
                x <= x;
                m<= m;
                n<=n;
            end
        end
        
    end
    // assert property (!((x>=n)&&(n>0)&&(m>=n)));
endmodule