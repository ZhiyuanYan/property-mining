module top (
    input wire selector,
    input wire clk,
    input wire rst,
    // output reg [10:0] n,
    // output reg [10:0] m,
    output reg [10:0] i,
    output reg [10:0] n,
    output reg [10:0] c
    
);

    always@(posedge clk) begin
        $display("i: %b, n: %b, c: %b", i, n, c);
    end 

    
    always @(posedge clk) begin
        if(rst)begin
            n<=150;
            i<=0;
            c<=0;
        end
        else begin
                if ((i>=n)) begin
                    i<=i;
                    c<=c;
                    n<=n;
                end

                else begin
                    i<=i+1;
                    c=c+i;
                    n<=n;
                end
            end
        end
    
    // assert property ((i<n)||(c>0));
endmodule