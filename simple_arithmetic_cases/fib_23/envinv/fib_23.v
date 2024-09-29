module top (
    input wire selector,
    input wire clk,
    input wire rst,
    // output reg [10:0] n,
    // output reg [10:0] m,
    output reg [10:0] i,
    output reg [10:0] n,
    output reg [10:0] sum
    
);

    always@(posedge clk) begin
        $display("i: %b, n: %b, sum: %b", i, n, sum);
    end 
    
    always @(posedge clk) begin
        if(rst)begin
            i<=0;
            sum<=0;
            n<=150;
        end
        else begin
                if ((i<n)) begin
                    i<=i+1;
                    sum<=sum+i;
                    n<=n;
                end
                // else if((i<n)) begin
                //     i<=i+1;
                //     j<=j;
                //     k<=k+10;
                // end
                else begin
                    i<=i;
                    sum<=sum;
                    n<=n;
                end
            end
        end
    
    // assert property ((i<n)||((sum>0)));
endmodule