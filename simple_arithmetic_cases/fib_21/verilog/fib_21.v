module top (
    input wire selector,
    input wire clk,
    input wire rst,
    // output reg [10:0] n,
    // output reg [10:0] m,
    output reg [10:0] i,
    output reg [10:0] n,
    output reg [10:0] k
    
);

    always@(posedge clk) begin
        $display("i: %b, n: %b, k: %b", i, n, k);
    end   
    
    always @(posedge clk) begin
        if(rst)begin
            i<=0;
            k<=0;
            n<=40;
        end
        else begin
                if ((i<n)) begin
                    i<=i+1;
                    n<=n;
                    k<=k+50;
                end
                // else if((i<n)) begin
                //     i<=i+1;
                //     j<=j;
                //     k<=k+10;
                // end
                else begin
                    i<=i;
                    n<=n;
                    k<=k;
                end
            end
        end
    
    // assert property ((i<n)||((k>n)));
endmodule